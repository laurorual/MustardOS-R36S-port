# C97 — primeiro boot após migração inicial C79

Data: 05/11/2026. Código próprio MIT. Nenhum código novo de upstream copiado;
refs permanecem somente leitura. Esta etapa separa a escrita física aprovada
do funcionamento da imagem instalada no R35S.

A migração C94 foi concluída no test128: escrita de512MiB somente na p2,
releitura fria, comparação integral do complemento MBR/p1/p3 e cópia independente
do novo registro de recuperação. Prova congelada `dist/phase4/p2-initial-native`.
A coleta foi retomada manualmente após verificar que o observador do host havia
encerrado antes de iniciá-la; o writer não foi repetido.

## Coleta somente leitura

`port/scripts/collect-phase4-initial-boot.py --host IP_DO_R35S` exige os recibos,
journal, pacote e fence C94 independentes antes de criar estágio ou executar SSH.
Confere a composição C93 e a imagem candidata regular novamente. Deriva o
primeiro contador esperado do fence, atualmente77→78, sem presumir que um
reboot extra do usuário equivale ao primeiro boot.

A guarda C76 só é reutilizada depois de comparar seus141arquivos com a árvore
da candidata C79: hash, arquivo regular, uid/gid0, link único, tamanho e modo.
São140arquivos públicos e uma chave pública de identidade estável; o busybox
mantém04755 explicitamente. A coleta verifica root0755/ext4 somente leitura,
p1/p3 desmontadas, PCM fechado, ausência de UI, módulos Bluetooth e tokens.once.

O caminho de entropy reutiliza apenas o gerador e decodificador puros C91,
nunca seu main não qualificado. Confere consumo do seed sem crédito de2048bits,
readiness antes de salvar, novo seed creditável com metadados restritos,
ausência dos seeds anteriores, incluindo o seed NC da candidata, e quatro
arquivos de identidade estável. Não imprime nem exporta esses dados privados.

Não escreve no console, reinicia, altera configurações ou rearma testes.
Qualquer divergência conserva stdout/stderr/script/vínculos privados em
`build/phase4/initial-boot/collect.*`; não autoriza reboot ou regravação automática.

## Verificação e limites

25casos passaram em container isolado: inventário real da candidata, arquivos
alterados/ausentes, links, modos, proprietário, tamanho, hash da identidade,
sintaxe shell, contador, campos duplicados/ausentes/desconhecidos, rotação e
recusa de SSH antes da coleta C94. Fontes estão vinculadas por hash em
`build/phase4/initial-boot/checks.iqf0zim8`.

Após conclusão C94, o caminho positivo de `lineage()` passou com os recibos e
imagens reais, sem acessar o R35S. O primeiro boot e o main SSH positivo passaram
no R35S192.168.15.8, contador78. A primeira tentativa expirou antes de estabelecer
SSH (exit255/sem stdout); após ping e porta2222 confirmarem disponibilidade,
repetiu-se somente a leitura no mesmo boot. Coleta aprovada em
`initial-boot/collect.kz1a9jg7`, exit0, com256bytes de seed creditável novo;
tentativa anterior preservada em `initial-boot/collect.r9a0gvf9`.
Nenhum reboot ou escrita pelo coletor.

`package-phase4-initial-boot.py` deriva novamente lineage, script e vínculos,
confere recibos/fontes/provas e publica somente campos permitidos em
`dist/phase4/initial-boot-native`. Não exporta boot ID, shell gerado, fence,
hashes de seeds/identidade/imagens ou os vínculos privados dos testes.
Os scripts gerados, manifestos privados e hashes de identidade não pertencem
à prova pública. Não repetir testes antigos de áudio/jogos sem divergência.
