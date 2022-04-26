# Introducción 
Este módulo se usa para importar extractos bancarios de Banco BHD León.

# Consideraciones

1. Se debe seleccionar la opción **Importar (OFX,TXT)** en la opción **Conexiones Bancarias** del Diario.
2. El unique ID que se le coloca a cada transacción es una combinación de FECHA+MONTO+DESCRIPCIÓN+REFERENCIA+SALDO. Si más de una transacción coinciden con esta combinación, las duplicadas no serán importadas.