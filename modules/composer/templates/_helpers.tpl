{{- define "helpers.configmap-key" }}
    {{- $path := "" }}
    {{- $data := "" }}
    {{- if .conf.dir }}
        {{- $path = .conf.dir }}
        {{- range $path, $content := $.Files.Glob (printf "%s/**" .conf.dir) }}
            {{- $data = printf "%s\n%s" $data $content }}
        {{- end }}
        {{- $data = tpl $data $ }}
    {{- else }}
        {{- $path = .conf.path }}
        {{- $data = tpl (toYaml .conf) . }}
    {{- end }}
    {{- $path = lower $path | replace "/" "-" | replace "." "-" | replace "_" "-" }}
    {{- trunc 63 (printf "%s%s-%s" .Release.Name $path ($data | sha1sum)) }}
{{- end }}

{{- define "helpers.secret-env" -}}
    {{- range $key, $value := .Values.secretEnv }}
        {{ $key }}: {{ tpl (toString $value) $ | b64enc }}
    {{- end }}
{{- end }}

{{- define "helpers.secret-env-key" }}
    {{- trunc 63 (printf "%s-env-%s" .Release.Name (include "helpers.secret-env" . | sha1sum)) }}
{{- end }}
