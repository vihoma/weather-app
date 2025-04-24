# Weather Query Python Program for the Command Line

- At the moment using OpenWeatherMap API with the PyOWM module
- Later some others perhaps...

## Usage

1. Install required packages: `pip install pyowm python-dotenv`

2. Create a `.weather.env` file in the home directory or the same directory
as this script and add your OWM_API_KEY and OWM_UNITS variables.
If you don't want to use a `.weather.env` file, you can set the environment
variables directly in your operating system or IDE.
For example:

    - In a Unix-like system, you can set them like this:

    ```bash
    export OWM_API_KEY=your_api_key_here
    export OWM_UNITS=metric
    ```

    - In Windows, you can set them like this:

    ```powershell
    New-Variable -Name OWM_API_KEY -Value your_api_key_here
    New-Variable -Name OWM_UNITS -Value metric
    ```

3. Run the program with `python weather.py`.
