{{- define "linuxserver.gpu-render-group" -}}
#!/usr/bin/with-contenv bash
# https://github.com/linuxserver/docker-plex/blob/177088c2988aa610d0a5b81a3525e08e40d79b36/root/etc/cont-init.d/50-gid-video
# check for the existence of a video and/or tuner device
if [ -e /dev/dri ] || [ -e /dev/dvb ]; then
	if [ -e /dev/dri ]; then
	FILES="${FILES} /dev/dri/*"
	fi
	if [ -e /dev/dvb ]; then
	FILES="${FILES} /dev/dvb/*"
	fi
else
	exit 0
fi

for i in $FILES
do
	VIDEO_GID=$(stat -c '%g' "$i")
	if id -G {{ .Values.gpu.user }} | grep -qw "$VIDEO_GID"; then
		touch /groupadd
	else
		if [ ! "${VIDEO_GID}" == '0' ]; then
			VIDEO_NAME=$(getent group "${VIDEO_GID}" | awk -F: '{print $1}')
			if [ -z "${VIDEO_NAME}" ]; then
				VIDEO_NAME="video$(head /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c8)"
				groupadd "$VIDEO_NAME"
				groupmod -g "$VIDEO_GID" "$VIDEO_NAME"
			fi
			usermod -a -G "$VIDEO_NAME" {{ .Values.gpu.user }}
			touch /groupadd
		fi
	fi
done

if [ ! -z "${FILES}" ] && [ ! -f "/groupadd" ]; then
	usermod -a -G root {{ .Values.gpu.user }}
fi
{{- end }}