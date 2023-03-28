import brownie
import json
import pytest

from brownie import accounts, Contract, Donator, Wei

from util.network_functions import get_network
from util.network_functions import is_local_network

@pytest.fixture(scope="module", autouse=True)
def tokens():
    network = get_network()

    script_config = json.load(open("config.json"))
    assert network in script_config, "Network configuration not found"

    network_config = script_config[network]

    abi_prize_token = json.loads(open("abis/PrizeToken_SPETHWIN.json").read())
    spethwin_token = Contract.from_abi("PrizeToken", network_config["prize_token"], abi_prize_token)

    abi_base_token = json.loads(open("abis/BaseToken_stETH.json").read())
    steth_token = Contract.from_abi("BaseToken", network_config["base_token"], abi_base_token)

    return spethwin_token, steth_token

@pytest.fixture(scope="module", autouse=True)
def deploy():
    network = get_network()

    script_config = json.load(open("config.json"))
    assert network in script_config, "Network configuration not found"

    network_config = script_config[network]

    assert is_local_network(), "Not on a forked network, below script will not work"

    account = accounts.at("0x42cd8312D2BCe04277dD5161832460e95b24262E", force=True)

    donator = Donator.deploy(
        network_config["stake_prize_pool"],
        network_config["prize_token"],
        network_config["base_token"],
        network_config["pool"],
        network_config["recipient"],
        {"from": account},
    )
    donator.setMinimumPrice(
        99 * 10 ** 16,
        {"from": account},
    )

    return account, network_config, donator

@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

@pytest.fixture
def raid_pooltogether_treasure(tokens, deploy):
    spethwin_token, _ = tokens
    account, network_config, donator = deploy

    account_spethwin_balance = spethwin_token.balanceOf(account)
    assert account_spethwin_balance > 0

    spethwin_token.transfer(donator, spethwin_token.balanceOf(account), {"from": account})

    assert spethwin_token.balanceOf(account) == 0
    assert spethwin_token.balanceOf(donator) == account_spethwin_balance

    return account, network_config, donator

def test_set_minimum_price(deploy):
    account, network_config, donator = deploy

    with brownie.reverts("price-zero"):
        donator.setMinimumPrice(0)

    donator.setMinimumPrice(99 * 10 ** 16, {"from": account})

    assert donator.minimumPrice() == 990000000000000000
    assert donator.minimumPrice() / Wei("1 ether") == 0.99

def test_set_recipient_with_balance(raid_pooltogether_treasure):
    account, _, donator = raid_pooltogether_treasure

    with brownie.reverts("balance-not-zero"):
        donator.setRecipient(account)

def test_transfer_ownership(deploy):
    account, network_config, donator = deploy

    assert donator.owner() == account

    donator.transferOwnership(network_config["recipient"])

    assert donator.owner() == network_config["recipient"]

def test_donate(tokens, raid_pooltogether_treasure):
    spethwin_token, steth_token = tokens
    account, _, donator = raid_pooltogether_treasure

    donation_account = accounts.at(donator.recipient(), force=True)
    balance_before_donation = donation_account.balance()

    spethwin_balance_before = spethwin_token.balanceOf(donator)
    assert spethwin_balance_before > 0

    txn = donator.donate({"from": account})

    balance_after_donation = donation_account.balance()

    assert "BaseTokenWithdrawn" in txn.events.keys()
    assert "BaseTokenSwapped" in txn.events.keys()
    assert "EtherReceived" in txn.events.keys()
    assert "EtherDonated" in txn.events.keys()

    assert donator.balance() == 0
    assert balance_after_donation == balance_before_donation + txn.events["EtherDonated"]["amount"]
