### Scripts

[![CircleCI](https://circleci.com/gh/BenVosper/scripts/tree/master.svg?style=shield)](https://circleci.com/gh/BenVosper/scripts/tree/master)

#### Parameter Store

Utilities for interacting with AWS Parameter Store. `aws configure` should be run beforehand for proper operation.

##### Requirements

 - Python 3.5 or above
 - The [AWS CLI](https://aws.amazon.com/cli/)
 - A successful run of `aws configure`

------------------------------------

##### [`fetch_params`](https://github.com/BenVosper/scripts/blob/master/param_store/fetch_params/fetch_params.py)

Get the names and values of parameters whose names begin with a given prefix. Uses `aws ssm describe-parameters` and `get-parameters`, to compile names and values into a convenient format.

For example, passing the prefix `foo` would fetch parameters named `foo.A`, `foo.B` etc. but **not** `bar.foo`.

###### Usage

 - `python fetch_params.py foo`

   Writes matching parameters to STDOUT.


 - `python fetch_params.py foo -o parameters.json`

   Creates a file `parameters.json` to which matching parameters are written.

------------------------------------

##### [`set_param`](https://github.com/BenVosper/scripts/blob/feature/readme/param_store/set_param/set_param.py)

Create a parameter or update an existing one. Can also be used with an input file to create / update multiple parameters simultaneously.

###### Usage

 - `python set_param -p foo -v bar`

   Creates a parameter named `foo` with value `bar`. By default, uses the `SecureString` parameter type


 - `python set_param -p foo -v bar -t String`

   Creates a parameter named `foo` with value `bar` with type `String`. Valid types:
    - `String`
    - `StringList`
    - `SecureString`


 - `python set_param -p foo -v bang -o`

   Overwrite `foo`'s value to `bang`.


 - `python set_param -j parameters.json`

   Create or update parameters from the file `parameters.json` containing parameter data in the format:
   ```json
   [
      {
        "Name": "foo",
        "Value": "bar"
      },
      {
        "Name": "this",
        "Value": "that"
      }
    ]
    ```
      `Type` and `Overwrite` keys can also be included for each parameter. If omitted, these options default to `SecureString` and   `False`.

------------------------------------


#### Testing

The test suite can be run using:

`nosetests .\tests\`
