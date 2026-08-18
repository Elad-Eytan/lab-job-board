1.1 — Inspect all objects

PS C:\Users\Elad Eytan Feldman\Desktop\K8S project\lab-job-board> kubectl get all -n jobboard
NAME                                        READY   STATUS    RESTARTS   AGE
pod/applications-service-5dd8c5968f-7lh25   1/1     Running   0          44m
pod/applications-service-5dd8c5968f-z8b2n   1/1     Running   0          44m
pod/frontend-6bf6d77c4-dfcgk                1/1     Running   0          9m14s
pod/frontend-6bf6d77c4-xzqrz                1/1     Running   0          9m7s
pod/jobs-service-679766589d-6dclf           1/1     Running   0          35m
pod/jobs-service-679766589d-92d6p           1/1     Running   0          36m
pod/postgres-5b8d74874c-tr4cs               1/1     Running   0          44m

NAME                           TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
service/applications-service   ClusterIP   10.104.148.32    <none>        3001/TCP   44m
service/frontend               ClusterIP   10.101.237.241   <none>        80/TCP     44m
service/jobs-service           ClusterIP   10.108.70.113    <none>        8000/TCP   44m
service/postgres               ClusterIP   10.101.238.8     <none>        5432/TCP   44m

NAME                                   READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/applications-service   2/2     2            2           44m
deployment.apps/frontend               2/2     2            2           44m
deployment.apps/jobs-service           2/2     2            2           44m
deployment.apps/postgres               1/1     1            1           44m

NAME                                              DESIRED   CURRENT   READY   AGE
replicaset.apps/applications-service-5dd8c5968f   2         2         2       44m
replicaset.apps/frontend-6bf6d77c4                2         2         2       9m14s
replicaset.apps/jobs-service-679766589d           2         2         2       36m
replicaset.apps/postgres-5b8d74874c               1         1         1       44m

NAME                                                           REFERENCE                         TARGETS                        MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/applications-service-hpa   Deployment/applications-service   cpu: 2%/60%, memory: 14%/75%   2         6         2          44m
horizontalpodautoscaler.autoscaling/jobs-service-hpa           Deployment/jobs-service           cpu: 5%/60%, memory: 45%/75%   2         6         2          44m
PS C:\Users\Elad Eytan Feldman\Desktop\K8S project\lab-job-board> kubectl get pvc -n jobboard
NAME           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
postgres-pvc   Bound    pvc-f485366d-16f8-4d08-b173-10cc7573b850   1Gi        RWO            standard       <unset>                 44m
PS C:\Users\Elad Eytan Feldman\Desktop\K8S project\lab-job-board> kubectl get ingress -n jobboard
NAME                   CLASS   HOSTS   ADDRESS        PORTS   AGE
applications-ingress   nginx   *       192.168.49.2   80      44m
frontend-ingress       nginx   *       192.168.49.2   80      44m
jobs-ingress           nginx   *       192.168.49.2   80      44m
PS C:\Users\Elad Eytan Feldman\Desktop\K8S project\lab-job-board> kubectl get hpa -n jobboard
NAME                       REFERENCE                         TARGETS                        MINPODS   MAXPODS   REPLICAS   AGE
applications-service-hpa   Deployment/applications-service   cpu: 2%/60%, memory: 14%/75%   2         6         2          44m
jobs-service-hpa           Deployment/jobs-service           cpu: 5%/60%, memory: 45%/75%   2         6         2          44m


- What is the **READY** ratio for each Deployment?

for applications-service, frontend and jobs-service it's 2/2
for the DB it's only 1/1

- What is the **CLUSTER-IP** of each Service?

service/applications-service   ClusterIP   10.104.148.32
service/frontend               ClusterIP   10.101.237.241
service/jobs-service           ClusterIP   10.108.70.113
service/postgres               ClusterIP   10.101.238.8

- What storage class was assigned to `postgres-pvc`?

The storage class that was assigned to postgres is a standard PVC:

NAME           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
postgres-pvc   Bound    pvc-f485366d-16f8-4d08-b173-10cc7573b850   1Gi        RWO            standard       <unset>                 107m


1.2 — Describe a Pod

- What `initContainer` runs first and why?

The initContainer uses busybox:1.36. It runs first and checks whether PostgreSQL is ready, if not, it prints "Waiting for postgres..." every 2 seconds. 
Once PostgreSQL is up, the init container terminates.

- What do the `readinessProbe` and `livenessProbe` check?

The readinessProbe is a test that tells the pod whether all services have come up correctly. 
The livenessProbe keeps checking that the service is up and running.

Liveness:   http-get http://:8000/health delay=30s timeout=5s period=15s #success=1 #failure=3
Readiness:  http-get http://:8000/health delay=10s timeout=5s period=10s #success=1 #failure=3

- What is the difference between them? What happens if readiness fails vs liveness fails?

if readiness fails it will wait for 30 secounds and try again till is ready, Kubernetes does not restart it and the pod becomes NotReady, Kubernetes removes the Pod from the jobs-service Service endpoints and The Ingress and Service stop sending new requests to that Pod.

if liveness fails Kubernetes considers the container unhealthy, The kubelet terminates the container and will start a replacement inside the same pod, The container’s restart count increases.
The Pod normally keeps the same name and IP because only its container restarts.

1.3 — Exec into a pod

- What is the full DNS name of the `postgres` service? (format: `<svc>.<ns>.svc.cluster.local`)

postgres.jobboard.svc.cluster.local

- Why can pods use the short name `postgres` instead of the FQDN?

since kubernates has its own DNS called CoreDNS, it translates addreses inside the cluster.
CoreDNS has a DNS record for the Kubernetes Service named postgres in the jobboard namespace, so it returns that Service’s ClusterIP.

Task 2 — Kubernetes Networking & Ingress

2.1 — Trace an Ingress request:

Browser / curl
POST loaclhost:8080/api/applications/
JSON request body
        │
        ▼
NGINX Ingress Controller
ingress-nginx namespace
        │
        │ Matches: applications-ingress
        │ Path: /api/applications(/|$)(.*)
        │
        │ Rewrite:
        │ /api/applications/ → /applications/
        ▼
applications-service Service
Namespace: jobboard
Type: ClusterIP
Port: 3001
Target port: 3001
        │
        │ Selector:
        │ app: applications-service
        ▼
One Ready applications-service Pod
Pod port: 3001
        │
        │ Express receives:
        │ POST /applications/
        ▼
router.post("/")
        │
        │ Validates request body
        │ Generates UUID
        │ Executes INSERT query
        ▼
postgres Service:5432
        │
        ▼
PostgreSQL Pod
        │
        │ Returns inserted database row
        ▼
applications-service Pod
        │
        │ Express returns:
        │ HTTP 201 Created
        │ JSON application object
        ▼
NGINX Ingress Controller
        │
        ▼
Browser / curl

$body = @{
>>     job_id = "job-001"
>>     applicant_name = "Test User"
>>     applicant_email = "test@lab.com"
>> } | ConvertTo-Json -Compress
PS C:\Users\Elad Eytan Feldman\Desktop\K8S project\lab-job-board> 
PS C:\Users\Elad Eytan Feldman\Desktop\K8S project\lab-job-board> $body | curl.exe -sv -X POST "http://localhost:8080/api/applications/" `
>>     -H "Content-Type: application/json" `
>>     --data-binary "@-" `
>>     2>&1 | Select-String '< HTTP|Location|\{'

< HTTP/1.1 201 Created
{ [205 bytes data]
{"id":"76e060c1-54f5-45eb-8639-9dea7c18ea80","job_id":"job-001","applicant_name":"Test 
User","applicant_email":"test@lab.com","cover_letter":null,"status":"pending","created_at":"2026-08-16T11:36:28.158Z"}

2.2 — Why three Ingress objects?

- Explain the nginx ingress annotation `nginx.ingress.kubernetes.io/rewrite-target` and why you can only have one value per Ingress object.

the nginx.ingress.kubernetes.io/rewrite-target annotation redirect the request URI path before forwarding it to the backend service.
you can only have one value per ingress object since In Kubernetes, annotations are stored inside the metadata block as a standard Map (Key-Value pairs), The second key will simply overwrite the first one.

- What would break if you put both paths in a single Ingress with one `rewrite-target`?

The second key (Path) will simply overwrite the first one, then it will only use the secound key.

- What alternative architecture would allow a single Ingress? (Hint: think about URL path prefixes in the services themselves.)

The alternative architecture that allows a single Ingress object is to shift the routing responsibility to the backend services themselves by configuring them to natively accept the full URL path prefix.
In this setup, you completely remove the rewrite-target annotation from the Ingress object.


2.3 — NodePort vs ClusterIP vs LoadBalancer (4 pts)


| Type | Reachable from | Use case | Example in this lab |
|------|---------------|----------|---------------------|
| ClusterIP | Cluster | in cluser communication | all services are configured with clusterip |
| NodePort | inside and outside the cluster | testing and development | we connect to the frontend using the tunnel connected to the Frontend service |
| LoadBalancer | Cluster | load balance incoming traffic to all available pods | the services act as load ballencers |
| Ingress | outside the cluster | allow incomming truffic into the cluster | we have a configured ingress for connecting with the services |


3.1 — Inspect the PersistentVolumeClaim


- What is the `Reclaim Policy` of the bound PersistentVolume?

The Reclaim Policy of the bound PersistentVolume is "Delete".

NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                   STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE
pvc-f485366d-16f8-4d08-b173-10cc7573b850   1Gi        RWO            `Delete`           Bound    jobboard/postgres-pvc   standard       <unset>                          25h

- What does `Retain` vs `Delete` mean for data when the PVC is deleted?

The reclaim policy controls what happens to a PersistentVolume and its underlying storage after its bound PVC is deleted. 
With Delete, Kubernetes removes the PV and the storage provider deletes the underlying storage, so its data is normally lost. With Retain, the PV and underlying data are preserved. However, the retained PV is marked Released and is not automatically reusable by another Pod or PVC, an administrator must manually recover or prepare it for reuse.

- What is the `Access Mode` and why can't postgres use `ReadWriteMany`?

The access mode defines how a PersistentVolume may be mounted by Kubernetes nodes.
PostgreSQL uses ReadWriteOnce, allowing its storage to be mounted read-write by one node. 
It should not use ReadWriteMany to let multiple independent PostgreSQL Pods share the same data directory, because concurrent access to the database files could cause lock conflicts and data corruption. 
Multiple application Pods may still connect to PostgreSQL over the network because they do not mount its volume directly.

3.2 — Verify data persistence across pod restarts

{
    "title":  "K8s Persistence Test",
    "description":  "This job must survive a pod restart",
    "company":  "Lab Inc",
    "location":  "Kubernetes",
    "salary_range":  null,
    "id":  "3a8e593d-6b32-4df3-9247-2486423e79b6",
    "created_at":  "2026-08-17T10:48:36.688575Z"
}

When the PostgreSQL Pod was deleted or restarted, Kubernetes created a replacement Pod. 
The new Pod mounted the same PersistentVolumeClaim (PVC), which was still connected to the same PersistentVolume (PV). 
PostgreSQL stores its database files in this mounted volume, so the job record remained available after the old Pod disappeared. 
Restarting a Pod does not delete its PVC or PersistentVolume.

3.3 — Manual database backup from Kubernetes

**restore procedure**

First, I locate the fresh PostgreSQL Pod and copy the SQL backup into it. 
I then use kubectl exec to run psql inside the Pod. 
The PostgreSQL username, password, and database name are read from the Pod’s environment variables, which were populated from the Kubernetes Secret.

$PG_POD = kubectl get pods -n jobboard -l app=postgres -o jsonpath='{.items[0].metadata.name}'

kubectl cp .\k8s-backup-20260817_140130.sql `
    "jobboard/${PG_POD}:/tmp/k8s-backup.sql"

kubectl exec -n jobboard $PG_POD -- `
    sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/k8s-backup.sql'

kubectl exec -n jobboard $PG_POD -- `
    sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT title FROM jobs;"'


Task 4 — Scaling & Rolling Updates

4.1 — Manual scaling

- How does the Ingress distribute traffic across 4 replicas?

The Ingress matches the request path and routes the request toward the appropriate Kubernetes Service. 
The Service uses its label selector to identify the four matching, Ready Pods. 
Traffic is then load-balanced across those Pod endpoints, so different requests can be handled by different replicas. 
Pods that fail their readiness probe are removed from the available endpoints and do not receive traffic.

- What load-balancing algorithm does the nginx ingress use by default?

The default load-balancing algorithm used by the Kubernetes Ingress-NGINX Controller is 'round robin'.
round robin essentialy routes to the traffic to the pods one by one in a round, it dose not take into considiration how loded each pod is.

- Scale back to 2 replicas. What happens to in-flight requests?

before scaling back to 2 replicas kubernates waits untill the pods are done procceing requests and then it terminates 2 pods.
the kubelet will not terminate a pod that is currenly serving in-flight requests.


4.2 — Rolling update with zero downtime

- What does `maxSurge: 1, maxUnavailable: 0` mean?

With four desired replicas, maxSurge: 1 allows Kubernetes to temporarily create one additional Pod during the rollout, meaning there can be up to five Pods. 
maxUnavailable: 0 means none of the four required replicas may be unavailable during the update. 
Kubernetes waits for a new Pod to become Ready before terminating an old Pod. This helps provide a zero-downtime rollout.

- Draw a timeline of what happens during a rolling update for `replicas: 2, maxSurge: 1, maxUnavailable: 0`.

Configuration:
replicas: 2
maxSurge: 1
maxUnavailable: 0

Time    Old version            New version             Available Pods
----------------------------------------------------------------------
T0      Pod A, Pod B           None                    2

T1      Pod A, Pod B           Pod C starting          2
        Kubernetes creates one additional Pod.

T2      Pod A, Pod B           Pod C ready             3
        Kubernetes waits until Pod C is ready.

T3      Pod B                  Pod C ready             2
        Pod A is terminated.

T4      Pod B                  Pod C, Pod D starting   2
        Kubernetes creates the next new Pod.

T5      Pod B                  Pod C, Pod D ready      3
        Kubernetes waits until Pod D is ready.

T6      None                   Pod C, Pod D ready      2
        Pod B is terminated. The rollout is complete.

- How would you rollback if the new version was broken?

Kubernetes keeps the previous ReplicaSets, allowing the Deployment to roll back to an earlier revision.
To rollback to the previous version you will give out this command:
**kubectl rollout undo deployment/jobs-service -n jobboard**


4.3 — HorizontalPodAutoscaler

- What is the formula the HPA uses to calculate desired replicas?

The HPA multiplies the current number of replicas by the ratio between the current metric and the target metric, then rounds the result upward. 
For CPU-based scaling, utilization is calculated relative to each container’s requested CPU, not its CPU limit. 
The final value is restricted by the HPA’s configured minimum and maximum replica counts.

desiredReplicas = ceil(currentReplicas × currentMetricValue ÷ desiredMetricValue)

- What is `stabilizationWindowSeconds` and why is it important for scale-down?

stabilizationWindowSeconds defines how long the HPA remembers previous replica recommendations. During scale-down, it uses the highest recommendation from that window, preventing Pods from being removed immediately after a temporary reduction in load. 
This reduces scaling fluctuations and gives running requests and workloads time to finish safely.

- What happens if `metrics-server` is not installed? How would you diagnose this?

Without metrics-server, the HPA cannot retrieve CPU or memory metrics, so its target is displayed as <unknown> and it cannot make the required scaling calculation. 
I would diagnose it using kubectl describe hpa, kubectl top pods, and by checking the metrics-server Deployment and the v1beta1.metrics.k8s.io APIService. 
In Minikube, metrics-server can be installed using minikube addons enable metrics-server.

# Check the HPA status and events
kubectl describe hpa jobs-service -n jobboard

# Check whether metrics are available
kubectl top pods -n jobboard

# Check whether metrics-server is running
kubectl get deployment metrics-server -n kube-system
kubectl get pods -n kube-system -l k8s-app=metrics-server

# Check whether the Metrics API is registered and available
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl describe apiservice v1beta1.metrics.k8s.io

# enable it with:
minikube addons enable metrics-server


Task 5 — Secrets & ConfigMaps

5.1 — Inspect the Secret

- Kubernetes Secrets are base64-encoded, not encrypted. What does this mean for security?

Kubernetes stores Secret values in Base64 format so that binary and special-character data can be represented safely in YAML and JSON. 
Base64 is encoding, not encryption. Anyone who obtains the encoded value can decode it immediately, so it does not protect the password from an attacker. 
Security must come from RBAC permissions, restricting which Pods and users can access Secrets, TLS while data travels over the network, and enabling encryption at rest for Secrets stored in etcd. 
Secret YAML files should also never be committed to Git.

- Name **two** production solutions that provide real secret encryption in Kubernetes:
  1. A Kubernetes-native solution
  2. An external secrets manager

A Kubernetes-native solution is Bitnami Sealed Secrets, which encrypts Secret manifests so they can safely be stored in Git. 
An external solution is HashiCorp Vault, which stores and manages secrets outside the cluster and provides them to authorized Kubernetes workloads when needed.

- What is **Sealed Secrets** and how does it work?

A Sealed Secret is simply a Kubernetes Secret stored in encrypted form. 
You produce one with the kubeseal command-line tool, which locks down the data using the public key of a controller deployed inside your cluster. 
Because only that controller holds the matching private key, it alone can decrypt the sealed object and materialize it as a regular, usable Secret.

5.2 — Add a ConfigMap for app configuration


- What is the difference between `env` (individual key) and `envFrom` (all keys)?

With env, each environment variable is defined individually. Its value can be written directly or retrieved from one specific ConfigMap or Secret key. With envFrom, Kubernetes imports every key from a referenced ConfigMap or Secret and creates an environment variable for each key automatically.

- When would you use a ConfigMap vs a Secret?

A ConfigMap is used for non-sensitive application configuration, such as log levels, feature flags, service addresses, limits, and allowed origins. 
A Secret is used for sensitive values such as passwords, API keys, authentication tokens, certificates, and connection strings containing credentials. 
Secrets can be protected with stricter RBAC permissions and encryption at rest, but their values are only Base64-encoded by default.

- What happens to running pods when you update a ConfigMap? (Hint: it depends...)

ConfigMap updates do not automatically restart Pods. 
Values imported through env or envFrom remain unchanged in running containers, so the Pods must be restarted. 
ConfigMaps mounted as volumes are normally refreshed automatically, but the application must reread the updated files.


6.2 — Add a Kubernetes smoke test step

