#! /bin/bash
PROJECT_NAME="camelopardalis-467-1"

deactivate_gae () {
    if ! [ -z "$OLD_PS1" ]; then
        export PS1="$OLD_PS1"
    fi
    if [ "$1" == "destroy" ]; then
        echo "destroying project";
        destroy_project;
    fi
    unset deactivate_gae
    unset OLD_PS1
    gcloud config unset project
}

destroy_project() {
    if gcloud projects delete ${PROJECT_NAME}; then
        deactivate_gae
    else
        echo "could not destroy project" >&2
    fi
}

if ! which gcloud; then
    echo "must install gcloud from https://cloud.google.com/sdk/downloads" >&2
else
    if [ -z "$OLD_PS1" ]; then
        OLD_PS1=$PS1
    fi

    if ! gcloud projects describe $PROJECT_NAME 2>/dev/null; then
        # create the project if it does not already exist
        if ! gcloud projects create $PROJECT_NAME; then
            echo "could not create project..."
        fi
    fi

    # export the deactivate function
    export deactivate_gae

    # modify the current project being worked on
    export PS1="(${PROJECT_NAME})$OLD_PS1"

    # set that as the project to use
    gcloud config set project $PROJECT_NAME
fi
