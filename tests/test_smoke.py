#!/usr/bin/python3.5

import os

import pytest
from juju.model import Model


@pytest.mark.asyncio
async def test_deploy():
    # Get env variables
    charm_name = os.environ.get('CHARM_NAME')
    charm_build_dir = os.environ.get('CHARM_BUILD_DIR')
    # Generate paths to locally built charms
    charm_path = os.path.join(charm_build_dir, charm_name)

    model = Model()
    print('Connecting to model')
    await model.connect_current()
    print('Resetting model')
    await model.reset(force=True)

    try:
        print('Deploying slurm-controller')
        application = await model.deploy(
            charm_path,
            application_name='slurm-controller'
        )

        print('Waiting for active')
        await model.block_until(
            lambda: all(unit.workload_status == 'blocked'
                        for unit in application.units))

        print('Removing slurm-controller')
        await application.remove()
    finally:
        print('Disconnecting from model')
        await model.disconnect()
