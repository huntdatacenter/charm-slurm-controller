from socket import gethostname

from charms.slurm.helpers import MUNGE_SERVICE
from charms.slurm.helpers import MUNGE_KEY_PATH
from charms.slurm.helpers import SLURMD_SERVICE
from charms.slurm.helpers import SLURM_CONFIG_PATH
from charms.slurm.helpers import SLURMCTLD_SERVICE
from charms.slurm.helpers import render_munge_key
from charms.slurm.helpers import render_slurm_config
from charms.slurm.helpers import create_state_save_location

from charmhelpers.core.host import pwgen
from charmhelpers.core.host import service_stop
from charmhelpers.core.host import service_pause
from charmhelpers.core.host import service_start
from charmhelpers.core.host import service_restart
from charmhelpers.core.host import service_running
from charmhelpers.core.hookenv import config
from charmhelpers.core.hookenv import status_set
from charmhelpers.core.hookenv import unit_private_ip

from charms.reactive import when
from charms.reactive import when_not
from charms.reactive import only_once
from charms.reactive import set_state
from charms.reactive import remove_state
from charms.reactive import when_file_changed


@only_once()
@when('slurm.installed')
def initial_setup():
    status_set('maintenance', 'Initial setup of slurm-controller')
    # Disable slurmd on controller
    service_pause(SLURMD_SERVICE)
    # Setup munge key
    munge_key = pwgen(length=4096)
    config().update({'munge_key': munge_key})
    render_munge_key(config=config())


@when_not('slurm-cluster.available')
def missing_nodes():
    status_set('blocked', 'Missing relation to slurm-node')
    remove_state('slurm-controller.configured')
    service_stop(SLURMCTLD_SERVICE)


@when('slurm-cluster.changed')
def cluster_has_changed(*args):
    set_state('slurm-controller.changed')
    remove_state('slurm-controller.configured')


@when('slurm-cluster.available')
@when('slurm-controller.changed')
def configure_controller(cluster):
    status_set('maintenance', 'Configuring slurm-controller')
    # Get node configs
    nodes = cluster.get_nodes()
    partitions = cluster.get_partitions()
    config().update({
        'nodes': nodes,
        'partitions': partitions,
        'control_machine': gethostname(),
        'control_addr': unit_private_ip(),
    })
    # Setup slurm dirs and config
    create_state_save_location(config=config())
    render_slurm_config(config=config())
    # Make sure slurmctld is running
    if not service_running(SLURMCTLD_SERVICE):
        service_start(SLURMCTLD_SERVICE)
    # Send config to nodes
    cluster.send_controller_config(config=config())
    # Update states
    remove_state('slurm-controller.changed')
    set_state('slurm-controller.configured')


@when('slurm-cluster.available', 'slurm-controller.configured')
def controller_ready(cluster):
    status_set('active', 'Ready')


@when_file_changed(SLURM_CONFIG_PATH)
def restart_on_slurm_change():
    service_restart(SLURMCTLD_SERVICE)


@when_file_changed(MUNGE_KEY_PATH)
def restart_on_munge_change():
    service_restart(MUNGE_SERVICE)
