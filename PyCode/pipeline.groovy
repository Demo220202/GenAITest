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
                    sh "python3 -m venv venv"
                    sh "source venv/bin/activate"
                    sh "pip install -r requirements.txt"
                    sh "python3 GenAI_automation.py --subscription_id $subscription_id --region $rg_region --deployment_model_name $dep_model_name --deployment_model_version $dep_model_version --brands $brand_names --client_id ARM_CLIENT_ID --client_secret ARM_CLIENT_SECRET --tenant_id ARM_TENANT_ID"
                }
            }
        }
        // stage ('Deployment Resource Creation'){
        //     steps{
        //         dir("PyCode"){
        //             sh "python3 GenAI_automation_P2.py"
        //         }
        //     }
        // }
        
        // stage ('DB Insertions'){
            
        //     steps{
        //         dir("PyCode"){
        //             sh "python3 AzureGenAIResourceDBInsertions.py env=$env brand=$brand_name subscription_id=$subscription_id rg_name=$rg_name user_email=$user_email"
        //         }
        //     }
        // }
    }
    post {
        success {
            dir('PyCode') {
                sh "cat output_json.json"
                sh "rm output_json.json"
                sh "deactivate"
                sh "rm -rf venv"

            }
        }
        failure {
            sh "pwd"
            dir('PyCode'){
                sh "python3 GenAI_automation_Revert.py --client_id ARM_CLIENT_ID --client_secret ARM_CLIENT_SECRET --tenant_id ARM_TENANT_ID"
                //sh "python3 GenAI_automation_P2_Revert.py <command_args>"
                sh "rm output_json.json"
                sh "deactivate"
                sh "rm -rf venv"
            }
        }
    }
}
