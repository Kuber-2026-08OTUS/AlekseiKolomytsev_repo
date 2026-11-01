{{/* Имя чарта */}}
{{- define "homework.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Полное имя ресурса */}}
{{- define "homework.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/* Имя ServiceAccount для мониторинга */}}
{{- define "homework.saName" -}}
{{- printf "%s-monitoring" (include "homework.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Селекторные лейблы */}}
{{- define "homework.selectorLabels" -}}
app.kubernetes.io/name: {{ include "homework.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* Общие лейблы */}}
{{- define "homework.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{ include "homework.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* Имя PVC */}}
{{- define "homework.pvcName" -}}
{{- if .Values.persistence.existingClaim -}}
{{- .Values.persistence.existingClaim -}}
{{- else -}}
{{- printf "%s-pvc" (include "homework.fullname" .) -}}
{{- end -}}
{{- end -}}