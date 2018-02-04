GCLOUD_PROJECT = $(shell gcloud config get-value project)
REGISTRY_HOST=us.gcr.io
IMAGE_NAME=camelopardalis
TAG_NAME=dev
VM_NAME=camelopardalis-vm

all:
	@echo "makefile to deploy to gcp"

.PHONY: deploy-image
deploy-image:
	docker build -t ${IMAGE_NAME} .
	docker tag ${IMAGE_NAME} ${REGISTRY_HOST}/${GCLOUD_PROJECT}/${IMAGE_NAME}/${TAG_NAME}
	gcloud docker -- push ${REGISTRY_HOST}/${GCLOUD_PROJECT}/${IMAGE_NAME}/${TAG_NAME}

.state-created-image: deploy-image
	touch $@

.state-image-deployed: .state-created-image
	touch $@


# TODO: update this with an ingress firewall rule that enables access to
# port 3000. Or better yet, proxy to nginx
.PHONY: create-container-vm
create-container-vm: .state-image-deployed
	gcloud beta compute instances create-with-container ${VM_NAME} --container-image ${REGISTRY_HOST}/${GCLOUD_PROJECT}/${IMAGE_NAME}/${TAG_NAME}
