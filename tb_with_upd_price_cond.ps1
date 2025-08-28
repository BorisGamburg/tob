param (
    [string]$symbol,
    [string]$config,
    [double]$offset,
    [int]$iterations = 1
)

Write-Host "Script execution started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Parameters: symbol=$symbol, config=$config, offset=$offset, iterations=$iterations"

function Invoke-TbPy {
    param ([string]$configFile)
    Write-Host "Running tb_bg.py with configuration: $configFile"
    # Execute the Python script and capture its exit code
    #python tb_bg.py --config $configFile
    python tb_bg.py --config $configFile
    $exitCode = $LASTEXITCODE

    # Check if the last command (python) was successful
    if (-not $?) {
        Write-Error "Error running tb.py with configuration $configFile. Exit code: $exitCode"
        return $false
    }
    Write-Host "tb.py executed successfully"
    return $true
}

Write-Host "Checking for configuration file existence: $config"
if (-not (Test-Path $config)) {
    Write-Error "Configuration file $config not found"
    exit 1
}

Write-Host "Initial Invoke-TbPy run"
if (-not (Invoke-TbPy -configFile $config)) {
    Write-Host "Aborting due to error in initial tb.py run"
    exit 1
}

$count = 0
while ($count -lt $iterations) {
    Write-Host "Iteration $count of $iterations"
    Write-Host "Getting price for symbol: $symbol"

    # Execute the Python script to get the current price
    $price_condition = python get_cur_price.py $symbol
    $exitCode = $LASTEXITCODE

    # Check if the Python script executed successfully
    if (-not $?) {
        Write-Error "Failed to get price for $symbol. Exit code: $exitCode"
        exit 1
    }
    Write-Host "Price received: $price_condition"

    try {
        # Convert the price to a double
        $price_condition = [double]$price_condition
        Write-Host "Price converted to number: $price_condition"
    }
    catch {
        # Handle conversion errors
        Write-Error "Invalid price from get_cur_price.py: $price_condition. Error: $_"
        exit 1
    }

    # Calculate the new price condition
    $price_condition = $price_condition * $offset
    $price_condition = "> $price_condition" # Format as a string for the config file
    Write-Host "Updated price condition: $price_condition"

    Write-Host "Updating configuration: $config"
    # Execute the Python script to set the config parameter
    python set_config_param.py $config price_condition $price_condition string
    $exitCode = $LASTEXITCODE

    # Check if the Python script executed successfully
    if (-not $?) {
        Write-Error "Failed to set configuration parameter in $config. Exit code: $exitCode"
        exit 1
    }
    Write-Host "Configuration updated successfully"

    Write-Host "Re-running Invoke-TbPy"
    if (-not (Invoke-TbPy -configFile $config)) {
        Write-Host "Aborting due to error in Invoke-TbPy"
        exit 1
    }

    $count++
}
Write-Host "Script completed successfully: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
