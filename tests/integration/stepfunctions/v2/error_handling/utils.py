from localstack.testing.snapshots.transformer import RegexTransformer
from localstack.utils.strings import short_uid
from tests.integration.stepfunctions.utils import await_execution_success


@staticmethod
def _test_sfn_scenario(
    stepfunctions_client,
    create_iam_role_for_sfn,
    create_state_machine,
    snapshot,
    definition,
    execution_input,
):
    snf_role_arn = create_iam_role_for_sfn()
    snapshot.add_transformer(RegexTransformer(snf_role_arn, "snf_role_arn"))
    snapshot.add_transformer(
        RegexTransformer(
            "Extended Request ID: [a-zA-Z0-9-/=+]+",
            "Extended Request ID: <extended_request_id>",
        )
    )
    snapshot.add_transformer(
        RegexTransformer("Request ID: [a-zA-Z0-9-]+", "Request ID: <request_id>")
    )

    sm_name: str = f"statemachine_{short_uid()}"
    creation_resp = create_state_machine(name=sm_name, definition=definition, roleArn=snf_role_arn)
    snapshot.add_transformer(snapshot.transform.sfn_sm_create_arn(creation_resp, 0))
    state_machine_arn = creation_resp["stateMachineArn"]

    exec_resp = stepfunctions_client.start_execution(
        stateMachineArn=state_machine_arn, input=execution_input
    )
    snapshot.add_transformer(snapshot.transform.sfn_sm_exec_arn(exec_resp, 0))
    execution_arn = exec_resp["executionArn"]

    await_execution_success(stepfunctions_client=stepfunctions_client, execution_arn=execution_arn)

    get_execution_history = stepfunctions_client.get_execution_history(executionArn=execution_arn)
    snapshot.match("get_execution_history", get_execution_history)
