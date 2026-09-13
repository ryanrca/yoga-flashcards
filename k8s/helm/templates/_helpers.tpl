{{/* Expand the name of the chart. */}}
{{- define "yoga-flashcards.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Fully qualified app name. */}}
{{- define "yoga-flashcards.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "yoga-flashcards.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "yoga-flashcards.labels" -}}
helm.sh/chart: {{ include "yoga-flashcards.chart" . }}
{{ include "yoga-flashcards.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "yoga-flashcards.selectorLabels" -}}
app.kubernetes.io/name: {{ include "yoga-flashcards.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "yoga-flashcards.backend.fullname" -}}
{{- printf "%s-backend" (include "yoga-flashcards.fullname" .) }}
{{- end }}

{{- define "yoga-flashcards.frontend.fullname" -}}
{{- printf "%s-frontend" (include "yoga-flashcards.fullname" .) }}
{{- end }}

{{- define "yoga-flashcards.mysql.fullname" -}}
{{- printf "%s-mysql" (include "yoga-flashcards.fullname" .) }}
{{- end }}

{{- define "yoga-flashcards.secretName" -}}
{{- if .Values.auth.existingSecret }}
{{- .Values.auth.existingSecret }}
{{- else }}
{{- printf "%s-secrets" (include "yoga-flashcards.fullname" .) }}
{{- end }}
{{- end }}

{{- define "yoga-flashcards.imageTag" -}}
{{- default .Chart.AppVersion .Values.image.tag }}
{{- end }}

{{- define "yoga-flashcards.backendImage" -}}
{{- $reg := .Values.image.registry -}}
{{- $repo := .Values.image.backend.repository -}}
{{- $tag := include "yoga-flashcards.imageTag" . -}}
{{- if $reg }}{{ printf "%s/%s:%s" $reg $repo $tag }}{{ else }}{{ printf "%s:%s" $repo $tag }}{{ end }}
{{- end }}

{{- define "yoga-flashcards.frontendImage" -}}
{{- $reg := .Values.image.registry -}}
{{- $repo := .Values.image.frontend.repository -}}
{{- $tag := include "yoga-flashcards.imageTag" . -}}
{{- if $reg }}{{ printf "%s/%s:%s" $reg $repo $tag }}{{ else }}{{ printf "%s:%s" $repo $tag }}{{ end }}
{{- end }}

{{/*
Hostnames the backend answers to. The service name and localhost are needed
because kubelet probes address the pod directly, not through the ingress.
*/}}
{{- define "yoga-flashcards.allowedHosts" -}}
{{- $hosts := list .Values.host (include "yoga-flashcards.backend.fullname" .) "localhost" "127.0.0.1" -}}
{{- range .Values.django.extraAllowedHosts }}{{ $hosts = append $hosts . }}{{ end -}}
{{- join "," $hosts }}
{{- end }}

{{- define "yoga-flashcards.origin" -}}
{{- if .Values.ingress.tls.enabled }}https://{{ .Values.host }}{{ else }}http://{{ .Values.host }}{{ end }}
{{- end }}

{{- define "yoga-flashcards.tlsSecretName" -}}
{{- default (printf "%s-tls" (include "yoga-flashcards.fullname" .)) .Values.ingress.tls.secretName }}
{{- end }}

{{/*
Database URL. django-environ parses this; the password is injected separately
via MYSQL_PASSWORD so it never appears in a ConfigMap.
*/}}
{{- define "yoga-flashcards.databaseHost" -}}
{{- include "yoga-flashcards.mysql.fullname" . }}
{{- end }}

{{/*
Environment shared by the backend container, its migrate init container and the
seed Job.

MYSQL_PASSWORD is declared before DATABASE_URL so kubelet's $(VAR) expansion can
substitute it -- that keeps the password out of the ConfigMap. It is generated
alphanumeric precisely so it is safe to interpolate into a URL.
*/}}
{{- define "yoga-flashcards.backendEnv" -}}
- name: DB_HOST
  value: {{ include "yoga-flashcards.databaseHost" . | quote }}
- name: DB_PORT
  value: {{ .Values.mysql.port | quote }}
- name: MYSQL_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "yoga-flashcards.secretName" . }}
      key: MYSQL_PASSWORD
- name: DJANGO_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "yoga-flashcards.secretName" . }}
      key: DJANGO_SECRET_KEY
- name: DATABASE_URL
{{- if .Values.externalDatabaseUrl }}
  value: {{ .Values.externalDatabaseUrl | quote }}
{{- else }}
  value: "mysql://{{ .Values.mysql.user }}:$(MYSQL_PASSWORD)@{{ include "yoga-flashcards.databaseHost" . }}:{{ .Values.mysql.port }}/{{ .Values.mysql.database }}"
{{- end }}
- name: PYTHONUNBUFFERED
  value: "1"
{{- with .Values.backend.extraEnv }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{- define "yoga-flashcards.backendEnvFrom" -}}
- configMapRef:
    name: {{ include "yoga-flashcards.fullname" . }}-config
{{- end }}

{{/*
Where the OpenRouter API key lives.

Either the chart's own Secret (populated from .Values.openrouter.apiKey) or a
Secret the operator manages themselves.
*/}}
{{- define "yoga-flashcards.openrouterSecretName" -}}
{{- if .Values.openrouter.existingSecret -}}
{{ .Values.openrouter.existingSecret }}
{{- else -}}
{{ include "yoga-flashcards.secretName" . }}
{{- end -}}
{{- end }}

{{- define "yoga-flashcards.openrouterSecretKey" -}}
{{- if .Values.openrouter.existingSecret -}}
{{ .Values.openrouter.existingSecretKey }}
{{- else -}}
OPENROUTER_API_KEY
{{- end -}}
{{- end }}

{{/*
Emits "true" when an OpenRouter key is reachable: supplied in values, held in a
user-managed Secret, or already stored in the chart's Secret from an earlier
install. The CronJob is skipped otherwise -- scheduling a bot that can only fail
every ten minutes is worse than not scheduling it.

Callers must `trim` the result before comparing: a whitespace-only string is
truthy in Go templates.
*/}}
{{- define "yoga-flashcards.openrouterConfigured" -}}
{{- if .Values.openrouter.existingSecret -}}
true
{{- else if .Values.openrouter.apiKey -}}
true
{{- else -}}
{{- $existing := lookup "v1" "Secret" .Release.Namespace (include "yoga-flashcards.secretName" .) -}}
{{- if and $existing (index $existing.data "OPENROUTER_API_KEY") -}}
true
{{- end -}}
{{- end -}}
{{- end }}
