.PHONY: all

# S3 bucket in us-east-1 region
bucket=<ENTER BUCKET>
version=v1
project=multi-function-packager
profile=<ENTER AWS CLI PROFILE NAME>
region=us-east-1
stack-name=MultiFunctionPackager

package:
	export EVENT_TYPE=$(event_type); \
	WORK_DIR=${PWD}/stage/$$EVENT_TYPE; \
	echo $$WORK_DIR; \
	mkdir -p $$WORK_DIR && mkdir -p $$WORK_DIR/lib && mkdir -p dist; \
	cp -r lambda-functions/chainer-function/* $$WORK_DIR/; \
	jq -r 'with_entries(select(.key == env.EVENT_TYPE)) | .[] | .[] | .function_name' functions.json > $$EVENT_TYPE.tmp; \
	jq -r 'with_entries(select(.key == env.EVENT_TYPE))' functions.json > $$WORK_DIR/functions.json; \
	while read rec;do \
		echo $$rec; \
		cp -r -f discrete-functions/$$rec $$WORK_DIR/lib/; \
	done < $$EVENT_TYPE.tmp; \
	cd $$WORK_DIR && zip -FS -q -r ../../dist/LambdaChainer-$$EVENT_TYPE.zip * && cd ../

build:
	mkdir -p dist && cd lambda-functions/chainer-function && zip -FS -q -r ../../dist/chainer-function.zip * && cd ../..
	mkdir -p dist && cd lambda-functions/assembly-lambda-function && zip -FS -q -r ../../dist/assembly-lambda-function.zip * && cd ../..
	mkdir -p dist && cd lambda-functions/assembly-function && zip -FS -q -r ../../dist/assembly-function.zip * && cd ../..

	aws cloudformation package --template-file templates/deploy-template.yaml \
	--s3-bucket $(bucket) --s3-prefix $(project)/$(version)/lambda-functions \
	--output-template-file dist/deploy.yaml --profile $(profile)
	aws s3 cp dist/deploy.yaml s3://$(bucket)/$(project)/$(version)/template/ --acl $(acl) --profile $(profile); \

deploy:
		aws cloudformation deploy --template-file dist/deploy.yaml \
		--parameter-overrides BUCKET=$(bucket) \
		--capabilities=CAPABILITY_NAMED_IAM \
		--stack-name $(stack-name)-$(version) --profile $(profile) --region $(region)

all: build deploy

clean:
	rm -rf stage/*
	rm -rf dist/*
