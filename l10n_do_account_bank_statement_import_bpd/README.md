# Introducción 
Este módulo se usa para importar extractos bancarios de Banco Popular Dominicano.

# Consideraciones

1. Se debe seleccionar la opción **Importar (OFX,TXT)** en la opción **Conexiones Bancarias** del Diario.
2. El número de la cuenta bancaria del archivo, debe coincidir con el **Número de Cuenta de Banco del Diario** donde se hará la importación.
3. El unique ID que se le coloca a cada transacción es una combinación de FECHA+MONTO+DESCRIPCIÓN. Si más de una transacción coinciden con esta combinación, las duplicadas no serán importadas.