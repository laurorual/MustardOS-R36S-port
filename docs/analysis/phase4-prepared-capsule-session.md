# C109 — integração do preparador local

Data: 07/11/2026. Terceira parte da rodada agrupada C107–C111, com uma única
conferência física ao fim. Código próprio MIT; C105/C106 e o worker original
permanecem congelados. Sem nova imagem integral, reboot ou acesso ao Deck.

## Caminho executado

O harness envia cinco arquivos para inputs em uma cápsula tmpfs própria 0700:
quatro assets públicos fixados e a ROM privada. O C106 enviava 12 arquivos
nesse ponto, além dos metadados gerados pelo host. Agora o comando instalado
`/usr/libexec/muos-capsule-v3/prepare.sh prepare` copia sete bibliotecas da
instalação qualificada, chama stage C105 para os dez scripts e produz os
metadados, a identidade do snapshot e os manifestos no aparelho.

A ROM e os metadados ficam somente em RAM. O preparador marca tentativa/ready;
falha parcial não pode ser repetida sobre a mesma cápsula. O harness então
chama `caller.sh run`, mantendo supervisor/namespace/worker instalados,
restauração do snapshot existente e saída por hotkey. Não monta nem grava p3
para criar uma biblioteca de ROMs. Jogo 45s, worker 210s e supervisor 240s.

A observação exige boot81/UUID real, instalação C111, layout C102 e 178 hashes
com metadados, preservando c25_ready. Três mapas, PID/starttime/cmdline do
worker instalado e marcador run.once permanecem obrigatórios. O fechamento
agora também exige o marcador ready produzido pelo preparador.

## Verificação e medidas

22 casos locais passaram em `prepared-capsule-session/checks.ebuwz4o8`:
vínculos/boot/UUID, inventário 178, upload de somente cinco entradas, ausência
de metadados pelo host, entrypoints instalados e âncoras finitas. Incluem
identidade derivada do par core/ROM real contra o snapshot C63 e validação independente do intervalo amostrado e recusa de eventos ausentes,
duplicados, invertidos ou sem startup. Reutilizam por integridade os 44 casos
C111 (incluindo regressões C107/C108/C110); nenhum core/ROM/reboot/rede é executado pelos checks.

O watcher original continua com polling de um segundo. Somente lê os logs
para registrar quando observa seleção consumida e primeiro frame do jogo,
mais o startup reportado pelo muxretro. São intervalos diferentes: a primeira
medida inclui preparação após seleção e espera até observação; a segunda é
a inicialização interna do muxretro. Não mede o instante físico do botão A,
não limita atrasos do scheduler e não demonstra uma causa para demora.
`C44_FIRST_PRESENT seconds=45` continua sendo o limite da janela do jogo.

**Sessão nativa e física aprovadas:** `prepared-capsule-session/load.ky2c382i`,
observação `observe.w28rjklk`, mesmo boot81 em192.168.15.8. O usuário respondeu
“Tudo certo” ao teste de imagem/direcional/som, restauração Fn+L2 e saída
Fn+Start/retorno ao menu. Resposta privada vinculada à análise da mesma sessão.

O primeiro preparo C109 recusou o modo0755 incorreto antes de criar stage;
C110 corrigiu para0644 e C111 corrigiu o callback tmpfs final. Ambas as lacunas
agora têm regressões locais. A sessão aprovada usa explicitamente C111;
check/recusa vazia anteriores não são classificados como preparo positivo.

1284frames, hotkey0/expired0, três mapas e worker instalado confirmados.
Snapshot/inventários/metadados permanecem byte-idênticos ao C63, duas chamadas
status e uma exportação, sem QuickSave. Native/OPERATION/CLEANUP0 e todos os
recibos postflight/mount-health/caller-execution/cleanup/stopped-screen0.
RaizRO0755, PCMclosed, p1/p3off, UIoff/taint0; mixer/DRM/volume/brilho/
WirePlumber e preferências55/70 restaurados. PID/starttime da infraestrutura e
mountinfo global iguais, cápsula removida e página diagnóstica final escrita.

Intervalo observado seleção consumida→primeiro frame: **8,42s**, amostragem
nominal1s; startup interno do muxretro: **1373,11ms**. Não subtrair esses valores
para atribuir uma causa: têm limites/instantes diferentes e não existe medição
equivalente do C106 para comparação. O tempo físico entre A e frame não foi
medido. Analisador C77 original preservado:59,9401Hz recente e4underruns/
1546frames de áudio ausentes agregados. Esses contadores não localizam o evento
nem qualificam desempenho sustentado; som limpo/audível foi confirmado pelo
usuário. Fechamento por recibos autênticos preservou imagem C64 e SDK.

Prova sanitizada própria `dist/phase4/prepared-capsule-session`, com métricas,
checks/fontes, sem ROM, ELF, estado, seed ou UUID real. Histórico C105/C106 e
as três provas de instalação permanecem intactos.

## Limites

Não qualifica navegador geral, autostart, SRAM, novos saves, boot frio, Power,
suspend ou longa duração. Quatro assets públicos e a ROM ainda têm origem
no host. Próximo lote: pacote residente dos quatro assets públicos com hashes/
origem/licenças, instalação aditiva e integração, antes de um novo teste físico.
Isso visa deixar somente a ROM como input; não pressupõe montá-la de p3 ou
persistir conteúdo privado. Novo boot exige observação/vínculo próprio, sem
reutilizar UUID81 ou claims consumidos. Cenário de dongle continua adiado.
