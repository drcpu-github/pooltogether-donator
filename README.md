### PoolTogether Donator

This repository contains a simple contract which can be used to automate withdrawing the prize token from a PoolTogether prize pool, swapping the base token to Ether using a Curve pool and then donate the swapped Ether to a third-party address.

The contract can be deployed using `brownie run deploy --network <network>`.

Tests can be run using `brownie test --network <forked-network> --disable-warnings`.

Don't forget to complete the `config.example.json` file with all required addresses and rename it to `config.json`.
