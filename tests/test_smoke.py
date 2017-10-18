import os

import pytest
from juju.model import Model


@pytest.mark.asyncio
async def test_deploy():
    # Get env variables
    CHARM_NAME = os.environ.get('CHARM_NAME')
    CHARM_BUILD_DIR = os.environ.get('CHARM_BUILD_DIR')
    # Generate paths to locally built charms
    CHARM_PATH = os.path.join(CHARM_BUILD_DIR, CHARM_NAME)

    model = Model()
    print('Connecting to model')
    await model.connect_current()
    print('Resetting model')
    await model.reset(force=True)

    try:
        print('Deploying {}'.format(CHARM_NAME))
        application = await model.deploy(
            CHARM_PATH,
            application_name=CHARM_NAME
        )

        print('Waiting for active')
        await model.block_until(
            lambda: all(unit.workload_status == 'blocked'
                        for unit in application.units))

        print('Removing {}'.format(CHARM_NAME))
        await application.remove()
    finally:
        print('Disconnecting from model')
        await model.disconnect()
