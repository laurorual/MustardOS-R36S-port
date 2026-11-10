# C89 — recuperação física restrita à p2

O helper `port/scripts/phase4-p2-recover.py` prepara a qualificação da
recuperação antes da migração C79. Sua única operação é `recover`: restaurar
a árvore pública C76 do backup C82, preservando a identidade de rede,
substituindo os seeds antigos por um seed novo sem crédito e avançando o
contador. Não aceita a candidata inicial C88 como imagem de recuperação.

O código novo é MIT. Reutiliza os contratos locais C82–C87; as referências
upstream permanecem intactas. A implementação de bloqueio/transição do kernel
foi qualificada em loop real pelo C87 e no MMC real, sem payload, pelo C90.

## Pré-condições e transação

Antes de entregar o cartão ao console, um registro C84 exclusivo e sincronizado
declara conservadoramente que pode ter ocorrido um boot. O preparador C86
pós-boot exige esse registro existente. Uma nova captura física somente leitura
precisa passar no scanner C85 nativo e numa análise independente no host.
O compositor C85 então produz uma imagem regular de recuperação vinculada
exatamente a essa captura e ao backup C82 independente.

O preparador C89 recusa a ausência da captura antes de acessar SSH. Confere
provas, fontes testadas, backup, composição, kernel qualificado e proteções
do cartão; transfere somente um arquivo regular privado e o pacote finito.
A execução privilegiada ocorre localmente no Deck, pois o SSH não dispõe de
sudo sem senha. Não há servidor ou sudo iniciado pelo preparador.

O helper sela o código em `/run`, isola o namespace de montagem, identifica
somente o cartão test128 e reforça somente leitura. Reconfere todos os
artefatos do backup remoto e seu recibo independente, copia as imagens para
um estágio privado fora do cartão e recaptura a p2. Três scans de descritores
protegidos — backup, captura e candidata — derivam a elegibilidade antes
de desbloquear a escrita. São exigidos árvore pública/metadados idênticos,
identidade estável, históricos consumidos preservados, ausência de `.once`
ativo, seed.no-credit de 256 bytes diferente dos seeds anteriores e contador
igual ao máximo conhecido mais um.

O controlador C87 grava somente os 512 MiB da p2 no offset de 128 MiB.
Registra intenção durável antes de desbloquear, mantém p1/p3 somente leitura,
recusa escrita curta sem repetição e verifica fsync, hashes e releitura após
restaurar as proteções. O complemento inteiro, incluindo a p3 de cerca de
118 GiB, é lido e comparado em várias passagens: esta verificação pode demorar
bastante. Não se limita a amostras da p3.

Uma conclusão válida inclui um novo registro C84 para a próxima entrega ao
console. O coletor precisa copiar e verificar esse registro no host antes da
mudança física do cartão. A qualificação do boot após recuperação é uma etapa
separada; o helper não inicia o console nem credita ou carrega seeds no RNG.
Falhas conservam estágio, journal e snapshot, reforçam RO quando possível e
não provocam repetição ou rollback automático.

## Validação e estado físico

Passaram 21 casos de elegibilidade com ext4 reais de 32 MiB, 27 casos de
entrada/contexto/cópia/bootstrap, 22 de transporte e cinco do registro de
handoff. Os testes não executaram o corpo privilegiado completo contra mídia.
Não equivalem a uma recuperação física aprovada.

Em 04/11/2026, o registro de handoff da instalação C76 atual foi selado e
copiado no host antes de entregar o test128 ao R35S. O boot 73 foi observado
por SSH: CID correto, arquivos instalados conferidos, raiz root:root0755
somente leitura, p3 desmontada, PCM fechado, sem sessão gráfica ou `.once`
ativo e inicialização do RNG confirmada pelo kernel. O desligamento normal
foi solicitado. Ainda faltam captura física pós-boot, composição, execução
C89 e boot posterior à recuperação.

A C88 preparada com contador 72 ficou desatualizada após esse boot e não está
liberada para gravação. O cartão original de 32 GB, o backup C82 e as cápsulas
C83 permanecem preservados. O estado operacional e os caminhos privados
atuais ficam no [checkpoint](phase4-resume-checkpoint.md).
