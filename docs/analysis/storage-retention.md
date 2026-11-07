# Armazenamento e versionamento — 07/11/2026

O levantamento confirmou aproximadamente 41 GiB em `build/phase4`, 2,7 GiB
em `dist` e dezenas de raízes históricas completas. O repositório Git existia,
mas ainda não tinha commits. O código e a documentação agora têm um baseline
local, com a identidade fornecida pelo usuário. Não houve publicação remota.
O baseline inclui C104 aprovado e o rascunho C105 interrompido; isso não
qualifica C105 como instalado ou aprovado no aparelho.

## Fluxo adotado

Editar e versionar código/docs no mesmo checkout. Compilar apenas o componente
alterado com os SDKs existentes; scripts e ajustes de documentação não exigem
uma nova imagem de 512 MiB. Pacotes pequenos e recibos de instalação continuam
separados e imutáveis quando já vinculados a uma prova. Não sobrescrever uma
tentativa consumida nem reciclar seus arquivos privados.

O limite é de cinco marcos de firmware e até cinco checkpoints nomeados no Git.
O histórico compacto de fontes é uma exceção de auditoria: permite comparar
implementações e verificar os hashes registrados sem guardar uma raiz inteira
por commit. Git não substitui os backups privados nem as provas congeladas.
ROM, refs, build, dist, caches Python, chaves e dados de provisionamento ficam
fora do índice Git. As fontes históricas exigidas pelas provas são preservadas.

O inventário explícito está em
[`storage-retention.json`](../../port/packaging/storage-retention.json).

| Marco | Motivo de retenção |
| --- | --- |
| C64 | Imagem ancestral ainda exigida pelo fechamento da cadeia C77/C104 |
| C79 | Fábrica original e artefatos do cartão exigidos pela provisão/auditoria |
| C89 | Referência da recuperação física qualificada |
| C93 | Candidata efetivamente migrada, exigida pelos validadores C97/C103 |
| C100 | Fábrica corrigida para reconstrução com o layout instalado |

Há sete arquivos de imagem nesses cinco marcos: C79 precisa de fábrica,
imagem do cartão e releitura da p2 em seus caminhos históricos. São entradas
de auditoria/reconstrução, não autorização para regravá-las. A candidata C93
tem contador/seed já consumidos; C100 é fábrica sem provisão. Qualquer nova
gravação precisa do fluxo de provisão/recuperação correspondente.

Exceções adicionais: backup independente C82, prefixos privados C20/C95,
capturas físicas de referência/pós-boot, recibos e fences C89/C94, dois SDKs
instalados, downloads/fontes do kernel e bootloader atual. São dependências
concretas ou material de recuperação; não manter todas as raízes antigas
sob esse rótulo. As licenças e provas sanitizadas em `dist` permanecem intactas.

## Limpeza verificável

`phase4-storage-dependencies.py` executa somente o preparo offline vigente de
C104/C105. Bloqueia escrita, operações de rede e subprocessos, exceto
`git check-ignore --quiet` usado pela guarda da ROM. Registra arquivos lidos,
metadados consultados e entradas retornadas para a futura cápsula. Não chama
os runners SSH nem inicia serviços, jogo, compilador ou emulador.

`retain-phase4-builds.py` cruza esse conjunto com o inventário explícito.
Descarta cópias antigas de raízes, imagens e fontes/objetos repetidos do
bootloader, mantendo os arquivos necessários dentro de árvores parcialmente
podadas. Relatórios históricos, scripts, fontes originais, SDKs e backups são
preservados. Caminhos removidos que aparecem em relatórios históricos deixam
de ser artefatos disponíveis; para repetir aquele build antigo, reconstruí-lo
a partir de suas fontes/recipes. As provas e dependências do próximo passo
continuam verificáveis sem essa reconstrução.

O plano privado em `build/cleanup/retention-*.json` registra arquivos e
assinaturas antes da exclusão, hashes dos arquivos preservados, política e
ferramentas. A aplicação recusa alterações desde o plano, árvores montadas,
arquivos abertos observáveis, aliases de diretórios e tipos especiais. Links
simbólicos internos são removidos sem seguir seu destino; links físicos de
uma entrada protegida são preservados para manter seu `nlink`.
Processos do desktop que o kernel impede de inspecionar são tolerados somente
quando seu comando não referencia este projeto. Não executar durante builds.

Após a exclusão, o limpador reconfere hashes/metadados protegidos e a mesma
cadeia offline. Nove testes descartáveis cobrem remoção limitada, alteração
do candidato/entrada/política, arquivo aberto, links físicos/simbólicos,
alias de pai e recusa de seis versões. O ganho físico deve ser medido por
`df`, pois a soma de `du` inclui blocos compartilhados pelo Btrfs.

## Resultado da limpeza

Planos aplicados: `build/cleanup/retention-20261107T155500Z.json.gz` e
`retention-20261107T160455Z.json.gz`. O segundo removeu raízes de composição e
sysroots clonados para pacotes C60/C67/C75; os SDKs instalados permanecem.
Foram removidos **404.812 arquivos** de réplicas históricas. O primeiro plano
cobria 21,75 GiB alocados e o segundo aproximadamente 0,92 GiB.
O ganho físico total medido foi **12.623.597.568 bytes, aproximadamente 11,8 GiB**;
o Btrfs compartilhava parte dos blocos das cópias. O espaço disponível passou
de aproximadamente 30 para 42 GiB. `build/phase4` caiu de 41 para 18 GiB
na contagem de `du`, que inclui extents compartilhados. A cadeia offline permaneceu idêntica e
os 1.391 arquivos protegidos mantiveram SHA-256 e metadados ao fim da limpeza.
Relatórios, provas, backups e template de áudio foram preservados.
Nenhum cartão, referência upstream ou arquivo no Steam Deck foi alterado.

Os planos consumidos foram comprimidos com gzip e relidos integralmente
para conferir o conteúdo. Resumo em `build/cleanup/retention-summary.json`.
O relatório registra os hashes no instante da limpeza; alterações posteriores
no código C105 devem ser versionadas e receber novos testes, sem reutilizar o
plano consumido. O limpador leva cerca de dois minutos no inventário antigo;
futuras execuções têm muito menos arquivos para examinar.

## Console observado nesta retomada

R35S respondeu em 192.168.15.8, boot **80**, raiz ext4 RO0755. O usuário
inseriu o dongle durante o boot. O relatório original C07 registra falha
`usb-mode`: o dispositivo não retornou como `0bda:c820`; a reinserção física
recuperou a conexão. O fallback é previsto, mas a inserção durante o boot
segue como cenário separado ainda não qualificado. A correção anterior foi
aprovada com o dongle presente desde o início.

Não relaxar `c25_ready` porque o SSH voltou: o relatório de falha desse boot
é preservado. C104 permanece uma prova do boot79. Após a limpeza, o C105 criou um novo
contexto válido no boot81 e foi instalado, conforme seu relatório próprio.
A limpeza em si não exigiu reboot, migração ou uso do Steam Deck.
