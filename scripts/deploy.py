import json
import logging

from brownie import accounts, Donator, Wei

from util.logger import setup_stdout_logger

from util.network_functions import get_account
from util.network_functions import get_network

def main():
    setup_stdout_logger()

    network = get_network()

    script_config = json.load(open("config.json"))
    assert network in script_config, "Network configuration not found"

    network_config = script_config[network]

    account = get_account()

    logging.info(f"Deploying the donator contract")

    donator = Donator.deploy(
        network_config["stake_prize_pool"],
        network_config["prize_token"],
        network_config["base_token"],
        network_config["pool"],
        network_config["recipient"],
        {"from": account},
        publish_source=True,
    )
    donator.setMinimumPrice(
        99 * 10 ** 16,
        {"from": account},
    )

    logging.info(f"Deployed the donator contract at {donator}")
    logging.info(f"\tMinimum swap price of stETH to ETH is {donator.minimumPrice() / Wei('1 ether')}")
    logging.info(f"\tRecipient is {donator.recipient()}")
