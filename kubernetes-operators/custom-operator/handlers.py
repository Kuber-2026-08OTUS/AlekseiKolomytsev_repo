import kopf
import kubernetes
import yaml
from kubernetes import client, config

# Загружаем конфигурацию кластера
try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

@kopf.on.create('otus.homework', 'v1', 'mysqls')
def create_mysql(spec, name, namespace, logger, **kwargs):
    image = spec.get('image', 'mysql:8.0')
    database = spec.get('database', 'mydb')
    password = spec.get('password', 'secret')
    storage_size = spec.get('storage_size', '1Gi')

    # 1. Создаем PersistentVolume (кластерный ресурс)
    pv_name = f"{name}-pv"
    pv_manifest = {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {"name": pv_name},
        "spec": {
            "capacity": {"storage": storage_size},
            "accessModes": ["ReadWriteOnce"],
            "persistentVolumeReclaimPolicy": "Retain",
            "storageClassName": "",
            "hostPath": {"path": f"/tmp/{pv_name}"}
        }
    }
    try:
        client.CoreV1Api().create_persistent_volume(body=pv_manifest)
        logger.info(f"PV {pv_name} created")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise

    # 2. Создаем PVC
    pvc_name = f"{name}-pvc"
    pvc_manifest = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": pvc_name, "namespace": namespace},
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": storage_size}},
            "storageClassName": "",
            "volumeName": pv_name
        }
    }
    try:
        client.CoreV1Api().create_namespaced_persistent_volume_claim(namespace, body=pvc_manifest)
        logger.info(f"PVC {pvc_name} created")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise

    # 3. Создаем Deployment
    deployment_name = f"{name}-deployment"
    deployment_manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": deployment_name, "namespace": namespace},
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": name}},
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": {
                    "containers": [{
                        "name": "mysql",
                        "image": image,
                        "env": [
                            {"name": "MYSQL_ROOT_PASSWORD", "value": password},
                            {"name": "MYSQL_DATABASE", "value": database}
                        ],
                        "ports": [{"containerPort": 3306}],
                        "volumeMounts": [{"name": "mysql-storage", "mountPath": "/var/lib/mysql"}]
                    }],
                    "volumes": [{"name": "mysql-storage", "persistentVolumeClaim": {"claimName": pvc_name}}]
                }
            }
        }
    }
    try:
        client.AppsV1Api().create_namespaced_deployment(namespace, body=deployment_manifest)
        logger.info(f"Deployment {deployment_name} created")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise

    # 4. Создаем Service типа ClusterIP
    service_name = f"{name}-service"
    service_manifest = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": service_name, "namespace": namespace},
        "spec": {
            "type": "ClusterIP",
            "selector": {"app": name},
            "ports": [{"port": 3306, "targetPort": 3306}]
        }
    }
    try:
        client.CoreV1Api().create_namespaced_service(namespace, body=service_manifest)
        logger.info(f"Service {service_name} created")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise

    return {"message": f"MySQL {name} provisioned successfully"}


@kopf.on.delete('otus.homework', 'v1', 'mysqls')
def delete_mysql(spec, name, namespace, logger, **kwargs):
    # Удаляем PV вручную, так как он не namespaced и не подчищается автоматически через ownerReferences
    pv_name = f"{name}-pv"
    try:
        client.CoreV1Api().delete_persistent_volume(pv_name)
        logger.info(f"PV {pv_name} deleted")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 404:
            raise
