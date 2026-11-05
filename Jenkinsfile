pipeline {

    agent any

    environment {
        IMAGE_NAME = 'smartcare-mlops'
        IMAGE_TAG = 'latest'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Downloading source code...'
                checkout scm
            }
        }

        stage('Python Setup') {
            steps {
                echo 'Checking Python version...'
                sh '''
                    python3 --version
                    pip3 --version
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing project dependencies...'
                sh '''
                    pip3 install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running Pytest...'
                sh '''
                    python3 -m pytest -v
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building SmartCare Docker image...'
                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                '''
            }
        }

        stage('Verify Docker Image') {
            steps {
                echo 'Checking Docker image...'
                sh '''
                    docker images
                    docker inspect ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }
    }

    post {
        success {
            echo 'SmartCare CI Pipeline Completed Successfully!'
        }

        failure {
            echo 'Pipeline Failed! Check Jenkins Console Output.'
        }

        always {
            echo 'Jenkins Pipeline Execution Finished.'
        }
    }
}
