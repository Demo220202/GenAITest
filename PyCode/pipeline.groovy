pipeline{
    agent any
    environment {
        ARM_CLIENT_ID = credentials('ARM_CLIENT_ID')
        ARM_CLIENT_SECRET = credentials('ARM_CLIENT_SECRET')
        ARM_TENANT_ID = credentials('ARM_TENANT_ID')
    }
    stages{
        
        stage ('Resource Group and OpenAI Resource Creation'){
            steps{
                dir("PyCode"){
                    sh """
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        python3 GenAI_automation.py --subscription_id $subscription_id --region $rg_region --deployment_model_name $dep_model_name --deployment_model_version $dep_model_version --brands $brand_names
                    """
                }
            }
        }
    }
    post {
        success {
            dir('PyCode') {
                sh """
                    cat output_json.json
                    rm output_json.json
                    rm -rf venv
                """
            }
        }
        failure {
            dir('PyCode'){
                sh """
                    . venv/bin/activate
                    python3 GenAI_automation_Revert.py --subscription_id $subscription_id
                    rm output_json.json
                    rm -rf venv
                """
            }
        }
    }
}
