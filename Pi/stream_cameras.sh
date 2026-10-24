#!/bin/bash

output_url="udp://192.168.2.1"
base_port=50000
RESTART_COOLDOWN=3
STARTUP_STAGGER=2

TARGET_W=640
TARGET_H=480
TARGET_FPS=30

SECONDARY_W=640
SECONDARY_H=480
SECONDARY_FPS=15

MAX_CAMERAS=3

WATCHDOG_POLL=5
WATCHDOG_STALLS=3

FORMAT_PRIORITY=(H264 MJPG YUYV)

BYPATH=/dev/v4l/by-path

devnums=(0 4 6 8)


have_v4l2ctl() { command -v v4l2-ctl >/dev/null 2>&1; }

is_capture_device() {
    local dev=$1
    have_v4l2ctl || return 0
    v4l2-ctl -d "$dev" --list-formats-ext 2>/dev/null | grep -q "'.*'"
}

detect_fourcc() {
    local dev=$1 fmts fmt
    fmts=$(v4l2-ctl -d "$dev" --list-formats-ext 2>/dev/null)
    for fmt in "${FORMAT_PRIORITY[@]}"; do
        grep -q "'$fmt'" <<<"$fmts" && { echo "$fmt"; return; }
    done
    echo ""
}

sizes_for() {
    local dev=$1 fourcc=$2
    v4l2-ctl -d "$dev" --list-formats-ext 2>/dev/null | awk -v f="$fourcc" '
        /\[[0-9]+\]:/ { inblk = (index($0, "\x27" f "\x27") > 0) }
        inblk && /Size: Discrete/ {
            for (i = 1; i <= NF; i++)
                if ($i ~ /^[0-9]+x[0-9]+$/) print $i
        }'
}

pick_resolution() {
    local dev=$1 fourcc=$2 tw=$3 th=$4 list
    [ -z "$fourcc" ] && { echo ""; return; }
    list=$(sizes_for "$dev" "$fourcc")
    [ -z "$list" ] && { echo ""; return; }
    if grep -qx "${tw}x${th}" <<<"$list"; then
        echo "${tw}x${th}"; return
    fi
    echo "$list" | awk -Fx '{print $1*$2, $1"x"$2}' | sort -n | head -1 | awk '{print $2}'
}

build_args() {
    local node=$1 role=$2 fourcc res ifmt w h fps
    if [ "$role" = "secondary" ]; then
        w=$SECONDARY_W; h=$SECONDARY_H; fps=$SECONDARY_FPS
    else
        w=$TARGET_W; h=$TARGET_H; fps=$TARGET_FPS
    fi

    IN_ARGS="-hide_banner -loglevel warning -f v4l2"

    if ! have_v4l2ctl; then
        IN_ARGS="$IN_ARGS -input_format mjpeg"
        OUT_ARGS="-c:v copy -f mjpeg -flush_packets 1"
        CONFIG_DESC="[$role] mjpeg/copy (unprobed: v4l2-ctl missing)"
        return
    fi

    fourcc=$(detect_fourcc "$node")
    res=$(pick_resolution "$node" "$fourcc" "$w" "$h")

    case "$fourcc" in
        MJPG) ifmt="mjpeg";   OUT_ARGS="-c:v copy -f mjpeg -flush_packets 1" ;;
        H264) ifmt="h264";    OUT_ARGS="-c:v copy -f mpegts -flush_packets 1" ;;
        YUYV) ifmt="yuyv422"; OUT_ARGS="-c:v mjpeg -q:v 5 -f mjpeg -flush_packets 1" ;;
        *)    ifmt="";        OUT_ARGS="-c:v mjpeg -q:v 5 -f mjpeg -flush_packets 1" ;;
    esac

    [ -n "$ifmt" ] && IN_ARGS="$IN_ARGS -input_format $ifmt"
    [ -n "$res" ]  && IN_ARGS="$IN_ARGS -video_size $res"
    IN_ARGS="$IN_ARGS -framerate $fps"
    CONFIG_DESC="[$role] ${ifmt:-default} ${OUT_ARGS} @ ${res:-camera-default} ${fps}fps"
}

discover_links() {
    [ -d "$BYPATH" ] || return 1
    local prefixes prefix l node fmt chosen
    prefixes=$(for l in "$BYPATH"/*-video-index*; do
                   [ -e "$l" ] && printf '%s\n' "${l%-video-index*}"
               done | sort -u)
    [ -z "$prefixes" ] && return 1

    while IFS= read -r prefix; do
        [ -z "$prefix" ] && continue
        chosen=""
        for fmt in "${FORMAT_PRIORITY[@]}"; do
            for l in "$prefix"-video-index*; do
                [ -e "$l" ] || continue
                node=$(readlink -f "$l")
                is_capture_device "$node" || continue
                if v4l2-ctl -d "$node" --list-formats-ext 2>/dev/null | grep -q "'$fmt'"; then
                    chosen="$l"; break 2
                fi
            done
        done
        [ -n "$chosen" ] && printf '%s\n' "$chosen"
    done <<< "$prefixes"
}

stream_camera() {
    local link=$1 port=$2 role=$3 node fpid prog mt last stalls
    prog="/tmp/ffprog_${port}.txt"

    while true; do
        node=$(readlink -f "$link" 2>/dev/null)
        if [ -z "$node" ] || [[ ! -e "$node" ]]; then
            echo "[$link] missing, waiting..."
            sleep "$RESTART_COOLDOWN"
            continue
        fi

        build_args "$node" "$role"
        echo "Starting stream for $node -> $output_url:$port  $CONFIG_DESC"

        : > "$prog"
        ffmpeg -progress "$prog" $IN_ARGS -i "$node" $OUT_ARGS "$output_url:$port" &
        fpid=$!

        last=0; stalls=0
        while kill -0 "$fpid" 2>/dev/null; do
            sleep "$WATCHDOG_POLL"
            mt=$(stat -c %Y "$prog" 2>/dev/null || echo 0)
            if [ "$mt" = "$last" ]; then
                stalls=$((stalls + 1))
                if [ "$stalls" -ge "$WATCHDOG_STALLS" ]; then
                    echo "[$node] HANG: no progress for ~$((WATCHDOG_POLL * WATCHDOG_STALLS))s; killing ffmpeg"
                    kill -9 "$fpid" 2>/dev/null
                    break
                fi
            else
                last=$mt; stalls=0
            fi
        done

        wait "$fpid" 2>/dev/null
        status=$?
        echo "[$node] ffmpeg stopped (status $status); restarting in ${RESTART_COOLDOWN}s"
        sleep "$RESTART_COOLDOWN"
    done
}


echo "[init] Clearing any stale ffmpeg holders on the camera nodes..."
killall -q ffmpeg 2>/dev/null
sleep 1

if ! have_v4l2ctl; then
    echo "[init] WARNING: v4l2-ctl not installed (apt install v4l-utils); adaptive probing disabled."
fi

streams=()
if links=$(discover_links) && [ -n "$links" ]; then
    while IFS= read -r l; do [ -n "$l" ] && streams+=("$l"); done <<< "$links"
    echo "[init] Discovered ${#streams[@]} physical camera(s) via $BYPATH"
else
    echo "[init] $BYPATH unavailable; falling back to fixed devnums (${devnums[*]})"
    for dev in "${devnums[@]}"; do
        node="/dev/video$dev"
        [ -e "$node" ] || { echo "[init] $node not present, skipping."; continue; }
        is_capture_device "$node" || { echo "[init] $node not a capture node, skipping."; continue; }
        streams+=("$node")
    done
fi

if [ ${#streams[@]} -eq 0 ]; then
    echo "[init] No usable capture devices found. Check connections / 'v4l2-ctl --list-devices'."
    exit 1
fi

if [ "$MAX_CAMERAS" -gt 0 ] && [ ${#streams[@]} -gt "$MAX_CAMERAS" ]; then
    echo "[init] Capping to MAX_CAMERAS=$MAX_CAMERAS (keeping main; dropping $(( ${#streams[@]} - MAX_CAMERAS )) extra)"
    streams=("${streams[@]:0:$MAX_CAMERAS}")
fi

for i in "${!streams[@]}"; do
    s="${streams[$i]}"
    node=$(readlink -f "$s" 2>/dev/null); node=${node:-$s}
    [ "$i" -eq 0 ] && role="main" || role="secondary"
    build_args "$node" "$role"
    echo "[init] port $((base_port + i)): $s -> $node  $CONFIG_DESC"
done

pids=()
cleanup() {
    echo "[exit] Stopping all camera streams..."
    kill "${pids[@]}" 2>/dev/null
    killall -q ffmpeg 2>/dev/null
    rm -f /tmp/ffprog_*.txt
}
trap cleanup EXIT INT TERM

for i in "${!streams[@]}"; do
    port=$((base_port + i))
    [ "$i" -eq 0 ] && role="main" || role="secondary"
    stream_camera "${streams[$i]}" "$port" "$role" &
    pids+=($!)
    sleep "$STARTUP_STAGGER"
done

wait
