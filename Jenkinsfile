pipeline {
    agent {
        docker {
            image 'boisvert/python-build'
            args '-v /var/run/docker.sock:/var/run/docker.sock -u root'
        }
    }
    environment {
        DOCKER_TOKEN = credentials('alphagamedev-docker-token')
        WEBUI_VERSION = sh(returnStdout: true, script: "cat webui.json | jq '.VERSION' -cMr").trim()

        // MySQL stuff
        MYSQL_HOST = "hubby.internal"
        MYSQL_DATABASE = "alphagamebot"
        MYSQL_USER = "alphagamebot"
        MYSQL_PASSWORD = credentials('alphagamebot-mysql-password')
    }
    stages {
        stage('build') {
            steps {
                sh 'docker build -t alphagamedev/alphagamebot:webui-$WEBUI_VERSION .'
            }
        }
        stage('push') {
            when {
                // We ONLY want to push Docker images when we are in the master branch!
                branch 'master'
            }
            steps {
                echo "Pushing image to Docker Hub"
                sh 'echo $DOCKER_TOKEN | docker login -u alphagamedev --password-stdin'
                sh 'docker tag  alphagamedev/alphagamebot:webui-$WEBUI_VERSION alphagamedev/alphagamebot:webui-latest'
                sh 'docker push alphagamedev/alphagamebot:webui-$WEBUI_VERSION' // push tag latest version
                sh 'docker push alphagamedev/alphagamebot:webui-latest' // push tag latest
                sh 'docker logout'
            }
        }
        stage('deploy') {
            steps {
                // conditionally deploy
                sh "docker container stop alphagamebot-webui || true"
                sh "docker container rm alphagamebot-webui || true"
                sh "docker run -d \
                                --name alphagamebot-webui -e BUILD_NUMBER -p 5600:5000 \
                                -e MYSQL_HOST -e MYSQL_DATABASE -e MYSQL_USER -e MYSQL_PASSWORD \
                                --restart=always \
                                alphagamedev/alphagamebot:webui-$WEBUI_VERSION"
            }
        }
    } // stages
}