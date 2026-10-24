# sincronizar_estilo.ps1
# Copia el estilo comun (carpeta estilo-comun) a todos los capitulos.
# Edita SIEMPRE el estilo en estilo-comun y luego ejecuta:
#     .\sincronizar_estilo.ps1

$raiz = $PSScriptRoot
$origen = Join-Path $raiz 'estilo-comun'

# Busca las carpetas que empiezan por "cap" y tienen settings.py
$capitulos = Get-ChildItem -Path $raiz -Directory -Filter 'cap*' |
    Where-Object { Test-Path (Join-Path $_.FullName 'settings.py') }

foreach ($cap in $capitulos) {
    $destinoStatic = Join-Path $cap.FullName '_static\libro'
    $destinoPlantillas = Join-Path $cap.FullName '_templates\global'

    # Borra la copia anterior para que no queden archivos viejos
    if (Test-Path $destinoStatic) { Remove-Item $destinoStatic -Recurse -Force }
    if (Test-Path $destinoPlantillas) { Remove-Item $destinoPlantillas -Recurse -Force }

    # Crea las carpetas si no existen
    New-Item -ItemType Directory -Path (Split-Path $destinoStatic) -Force | Out-Null
    New-Item -ItemType Directory -Path (Split-Path $destinoPlantillas) -Force | Out-Null

    # Copia la version maestra
    Copy-Item (Join-Path $origen '_static\libro') $destinoStatic -Recurse
    Copy-Item (Join-Path $origen '_templates\global') $destinoPlantillas -Recurse

    Write-Host "Estilo actualizado en $($cap.Name)"
}