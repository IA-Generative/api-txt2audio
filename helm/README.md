# api-audio2txt

![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

A Helm chart to deploy the api-audio2txt service

## Values

### App

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| app.affinity | object | `{}` | Default affinity for app. |
| app.autoscaling.enabled | bool | `false` | Enable Horizontal Pod Autoscaler ([HPA]) for the app. |
| app.autoscaling.maxReplicas | int | `3` | Maximum number of replicas for the app [HPA]. |
| app.autoscaling.minReplicas | int | `1` | Minimum number of replicas for the app [HPA]. |
| app.autoscaling.targetCPUUtilizationPercentage | int | `80` | Average CPU utilization percentage for the app [HPA]. |
| app.autoscaling.targetMemoryUtilizationPercentage | int | `80` | Average memory utilization percentage for the app [HPA]. |
| app.container.args | list | `[]` | app container command args. |
| app.container.command | list | `[]` | app container command. |
| app.container.port | int | `8080` | app container port. |
| app.container.securityContext | object | `{}` | Toggle and define container-level security context. |
| app.env | object | `{}` | app container env variables, it will be injected into a configmap and loaded into the container. |
| app.envFrom | list | `[]` | app container env variables loaded from configmap or secret reference. |
| app.extraContainers | list | `[]` | Extra containers to add to the app pod as sidecars. |
| app.extraVolumeMounts | list | `[]` | List of extra mounts to add (normally used with extraVolumes). |
| app.extraVolumes | list | `[]` | List of extra volumes to add. |
| app.healthcheckPath | string | `"/"` | app container healthcheck endpoint. |
| app.hostAliases | list | `[]` | Host aliases that will be injected at pod-level into /etc/hosts. |
| app.image.pullPolicy | string | `"Always"` | Image pull policy for the app. |
| app.image.pullSecrets | list | `[]` | Image pull policy for the app. |
| app.image.repository | string | `"docker.io/debian"` | Repository to use for the app. |
| app.image.tag | string | `""` | Tag to use for the app. Overrides the image tag whose default is the chart appVersion. |
| app.ingress.annotations | object | `{}` | Additional ingress annotations. |
| app.ingress.className | string | `""` | Defines which ingress controller will implement the resource. |
| app.ingress.enabled | bool | `true` | Whether or not ingress should be enabled. |
| app.ingress.hosts | list | `[]` | The list of hosts to be covered by ingress record. |
| app.ingress.labels | object | `{}` | Additional ingress labels. |
| app.ingress.tls | list | `[]` | Enable TLS configuration. |
| app.initContainers | list | `[]` | Init containers to add to the app pod. |
| app.livenessProbe.enabled | bool | `true` | Whether or not enable the probe. |
| app.livenessProbe.failureThreshold | int | `3` | Minimum consecutive successes for the probe to be considered successful after having failed. |
| app.livenessProbe.initialDelaySeconds | int | `30` | Whether or not enable the probe. |
| app.livenessProbe.periodSeconds | int | `30` | Minimum consecutive failures for the probe to be considered failed after having succeeded. |
| app.livenessProbe.successThreshold | int | `1` | Number of seconds after the container has started before probe is initiated. |
| app.livenessProbe.timeoutSeconds | int | `5` | How often (in seconds) to perform the probe. |
| app.nodeSelector | object | `{}` | Default node selector for app. |
| app.podAnnotations | object | `{}` | Annotations for the app deployed pods. |
| app.podLabels | object | `{}` | Labels for the app deployed pods. |
| app.podSecurityContext | object | `{}` | Toggle and define pod-level security context. |
| app.serviceAccount.create | bool | `false` | Whether to create a dedicated service account for the application. |
| app.serviceAccount.name | string | `""` | Name of the service account to use. If not set and create is true, a name is generated using the release name. |
| app.readinessProbe.enabled | bool | `true` | Whether or not enable the probe. |
| app.readinessProbe.failureThreshold | int | `2` | Minimum consecutive failures for the probe to be considered failed after having succeeded. |
| app.readinessProbe.initialDelaySeconds | int | `15` | Number of seconds after the container has started before probe is initiated. |
| app.readinessProbe.periodSeconds | int | `10` | How often (in seconds) to perform the probe. |
| app.readinessProbe.successThreshold | int | `2` | Minimum consecutive successes for the probe to be considered successful after having failed. |
| app.readinessProbe.timeoutSeconds | int | `5` | Number of seconds after which the probe times out. |
| app.replicaCount | int | `1` | The number of application controller pods to run. |
| app.resources.limits.cpu | string | `"100m"` | CPU limit for the app. |
| app.resources.limits.memory | string | `"256Mi"` | Memory limit for the app. |
| app.resources.requests.cpu | string | `"100m"` | CPU request for the app. |
| app.resources.requests.memory | string | `"256Mi"` | Memory request for the app. |
| app.secrets | object | `{}` | app container env secrets, it will be injected into a secret and loaded into the container. |
| app.service.port | int | `80` | app service port. |
| app.service.type | string | `"ClusterIP"` | app service type. |
| app.startupProbe.enabled | bool | `true` | Whether or not enable the probe. |
| app.startupProbe.failureThreshold | int | `10` | Minimum consecutive failures for the probe to be considered failed after having succeeded. |
| app.startupProbe.initialDelaySeconds | int | `0` | Number of seconds after the container has started before probe is initiated. |
| app.startupProbe.periodSeconds | int | `10` | How often (in seconds) to perform the probe. |
| app.startupProbe.successThreshold | int | `1` | Minimum consecutive successes for the probe to be considered successful after having failed. |
| app.startupProbe.timeoutSeconds | int | `5` | Number of seconds after which the probe times out. |
| app.strategy.type | string | `"RollingUpdate"` | Strategy type used to replace old Pods by new ones, can be "Recreate" or "RollingUpdate". |
| app.tolerations | list | `[]` | Default tolerations for app. |
| app.viteEnv | object | `{}` | app container env variables, it will be injected into a configmap and loaded into the container as a volume. |

### General

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| extraObjects | list | `[]` | Add extra specs dynamically to this chart. |

### Global

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| global.env | object | `{}` | Map of environment variables to inject into backend and frontend containers. |
| global.secrets | object | `{}` | Map of environment variables to inject into backend and frontend containers. |

### VaultStaticSecrets

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| vaultStaticSecrets[0].annotations | object | `{}` | Additional annotations for VaultStaticSecret. |
| vaultStaticSecrets[0].destination.annotations | object | `{}` | Annotations to apply to the Secret. |
| vaultStaticSecrets[0].destination.create | bool | `true` | Create the destination Secret. If the Secret already exists this should be set to false. |
| vaultStaticSecrets[0].destination.labels | object | `{}` | Labels to apply to the Secret. |
| vaultStaticSecrets[0].destination.name | string | `""` | Name of the Secret. |
| vaultStaticSecrets[0].destination.overwrite | bool | `false` | Overwrite the destination Secret if it exists and Create is true. This is useful when migrating to VSO from a previous secret deployment strategy. |
| vaultStaticSecrets[0].destination.transformation | object | `{}` | Transformation provides configuration for transforming the secret data before it is stored in the Destination. |
| vaultStaticSecrets[0].destination.type | string | `"Opaque"` | Type of Kubernetes Secret. |
| vaultStaticSecrets[0].enabled | bool | `false` | Enabled the creation of the VaultStaticSecret. |
| vaultStaticSecrets[0].hmacSecretData | bool | `true` | HMACSecretData determines whether the Operator computes the HMAC of the Secret's data. The MAC value will be stored in the resource's Status.SecretMac field, and will be used for drift detection and during incoming Vault secret comparison. Enabling this feature is recommended to ensure that Secret's data stays consistent with Vault. |
| vaultStaticSecrets[0].labels | object | `{}` | Additional labels for VaultStaticSecret. |
| vaultStaticSecrets[0].mount | string | `""` | Mount for the secret in Vault. |
| vaultStaticSecrets[0].namespace | string | `""` | Namespace of the secrets engine mount in Vault. If not set, the namespace that's part of VaultAuth resource will be inferred. |
| vaultStaticSecrets[0].path | string | `""` | Path of the secret in Vault, corresponds to the `path`` parameter for, [kv-v1](https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v1#read-secret) or [kv-v2](https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#read-secret-version). |
| vaultStaticSecrets[0].refreshAfter | string | `""` | RefreshAfter a period of time, in duration notation e.g. 30s, 1m, 24h. |
| vaultStaticSecrets[0].rolloutRestartTargets | list | `[]` | RolloutRestartTargets should be configured whenever the application(s) consuming the Vault secret does not support dynamically reloading a rotated secret. In that case one, or more RolloutRestartTarget(s) can be configured here. The Operator will trigger a "rollout-restart" for each target whenever the Vault secret changes between reconciliation events. All configured targets will be ignored if HMACSecretData is set to false. See RolloutRestartTarget for more details. |
| vaultStaticSecrets[0].type | string | `"kv-v2"` | Type of the Vault static secret (should be `kv-v1` or `kv-v2`). |
| vaultStaticSecrets[0].vaultAuthRef | string | `""` | VaultAuthRef to the VaultAuth resource, can be prefixed with a namespace, eg: `namespaceA/vaultAuthRefB`. If no namespace prefix is provided it will default to the namespace of the VaultAuth CR. If no value is specified for VaultAuthRef the Operator will default to the default VaultAuth, configured in the operator's namespace. |
| vaultStaticSecrets[0].version | string | `nil` | Version of the secret to fetch. Corresponds to `version` query parameter: [version](https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#version). Only valid for type kv-v2. |

### Other Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| fullnameOverride | string | `""` | String to fully override the default application name. |
| nameOverride | string | `""` | Provide a name in place of the default application name. |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
