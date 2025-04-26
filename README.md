# Weather Query Python Program for the Command Line

- Uses the OpenWeatherMap API with the PyOWM module

## Usage

1. Install required packages: `pip install -r requirements.txt`

2. Create a `.weather.env` file in the home directory or the same directory
as this script and add your OWM_API_KEY variable.
If you don't want to use a `.weather.env` file, you can set the environment
variables directly in your operating system or IDE.
For example:

    - In a Unix-like system, you can set it like this:

    ```bash
    export OWM_API_KEY=your_api_key_here
    ```

    - In Windows, you can set it like this:

    ```powershell
    New-Variable -Name OWM_API_KEY -Value your_api_key_here
    ```

3. Run the program with `python weather.py`.
