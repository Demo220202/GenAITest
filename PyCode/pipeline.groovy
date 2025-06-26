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
                    sh '''
                        python3.10 -m venv venvgenai
                        . venvgenai/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        python3 GenAI_automation.py --subscription_id $subscription_id --region $rg_region --deployment_model_name $dep_model_name --deployment_model_version $dep_model_version --brands "$brand_names" --deployment_type $dep_type --env_m $env_main --email $user_email
                    '''
                }
            }
        }

        stage ('Deployment Resource Creation and Enabling Dynamic Quota'){
            steps{
                dir("PyCode"){
                    sh '''
                        . venvgenai/bin/activate
                        python3 GenAI_automation_P2.py
                    '''
                }
            }
        }


        stage ('DB Insertions'){

            steps{
                dir("PyCode"){
                    sh '''
                        . venvgenai/bin/activate
                        python3 GenAI_add_voices.py --env_m $env_main
                        python3 AzureGenAIResourceDBInsertions.py --env_m $env_main  --user_email $user_email
                        python3 GenAIPredictionWrapperDB.py --user_email $user_email --env_m $env_main
                        python3 ProdCoachDBInsertions.py --env $env_pa  --email $user_email --env_m $env_main
                    '''
                }
            }
        }

        stage ('Checking DB Conection!'){
            steps{
                dir("PyCode"){
                    sh '''
                        . venvgenai/bin/activate
                        python3 ProdDBConnCheck.py --env_m $env_main  --env_p $env_pa --user_email $user_email --brands "$brand_names"
                    '''
                }
            }
        }

        stage ('Creation of Action Group and Alerts'){
            steps{
                dir("PyCode"){
                    sh '''
                        . venvgenai/bin/activate
                        python3 ActionGroupNAlerts.py
                    '''
                }
            }
        }
        
    }
    post {
        success {
            dir('PyCode') {
                sh """
                   cat openai_resources.json
                   rm openai_resources.json
                   cat alert_resources.json || echo "alert_resources.json not found"
                   rm -f alert_resources.json
               """
            }
        }
        failure {
            dir('PyCode'){
               sh '''
                   . venvgenai/bin/activate
                   python3 GenAI_automation_P2_Revert.py
                   if [ -f alert_resources.json ]; then
                       python3 ActionGroupNAlerts_Revert.py
                   else
                       echo "alert_resources.json not found, skipping ActionGroupNAlerts_Revert.py"
                   fi
                   python3 GenAI_automation_Revert.py --subscription_id $subscription_id
                   rm -f openai_resources.json
                   rm -f alert_resources.json
               '''
            }
        }
    }
}
