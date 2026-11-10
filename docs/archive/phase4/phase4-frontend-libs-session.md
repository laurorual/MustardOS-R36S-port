# C66 — provider frontend qualificado em RAM no boot 71

Concluído em 03/11/2026, com o R35S em 192.168.15.10. As bibliotecas
produzidas no C65 passaram em execução nativa supervisionada: menu, Super
Mario Land, restauração Fn+L2, saída Fn+Start e retorno ao menu. O usuário
confirmou “Tudo certo!”. Não houve instalação das bibliotecas, novo save,
reboot solicitado, alteração da imagem ou acesso ao cartão original/Deck.

## Por que um vínculo novo

A inspeção inicial encontrou kernel 4.4.189-muos-r35s-p4, raiz ext4 somente
leitura e boot 71 com UUID diferente do boot 70 dos recibos C63. O C63 antigo
continua exigindo seu boot/UUID originais; não foi editado ou executado
contra o novo boot.

O módulo phase4_frontend_libs_session.py verifica a prova C63 congelada e
executa somente o prefixo offline do runner, cortado antes de qualquer SSH
ou alocação. Esse prefixo valida os assets e vínculos C53–C63 com o boot
histórico 70. Só então o C66 usa uma observação nova, com contador inteiro,
UUID exato, IP, hashes dos recibos C63/C65 e infraestrutura PID/starttime.
Os três testes de contador do preflight são derivados para 71; a guarda
do UUID observado é aplicada a cada operação remota.

O observador não ativa serviços. Confere card guard, fundação97, pré-requisitos
C62/105 e treze arquivos instalados com hashes/modos. O fechamento também
amarra identidade/assets privados aos inputs históricos e compara os
inventários de store C54/C58/C61/C63. Nenhum vínculo histórico foi transformado
em uma alegação de “mesmo boot” para o C66.

## Delta runtime

Código próprio MIT em port/device/rk-r35s-p0/frontend-libs-session/ e nos
scripts prepare/check/run/analyze/finish/package-phase4-frontend-libs-session.py.
O worker, runner de processos, sessão GB, backend load-only e os seletores
continuam com os bytes históricos aprovados. Os testes de lifecycle C45 e
104 checks C63 são reutilizados com seus hashes; não foram repetidos.

O renderer acrescenta ao launcher C63 apenas o ambiente fixo das bibliotecas
do app; ao dispatcher instalado acrescenta uma chamada ao guard C66. Os
treze hashes e verificações do host instalado continuam iguais. A cápsula
não contém ELF muxretro ou save-store, nem alternativa para o host instalado.

Há dois conjuntos em RAM:

| Processo | Bibliotecas usadas |
| --- | --- |
| Menus inicial e de retorno | C65 libui/libmuxcom/libplutosvg em capsule/lib; libmuxmod diagnóstica C46 preservada |
| muxretro instalado/jogo | Quatro bibliotecas C65 em capsule/provider-lib |
| Demais serviços | Ambiente e bibliotecas originais do worker |

O guard fixa os sete arquivos, hashes, modo700/root:root/link1, diretórios
root700 sem symlinks e tmpfs. Em launch exige LD_BIND_NOW e o caminho exato
do provider. Não aceita outro executável, operação de escrita ou parâmetros
de lançamento. O guard C63 continua validando role load, conteúdo em RAM e
pacote instalado antes do exec absoluto.

No novo boot foram executados o probe eager das quatro bibliotecas e
version/help do host instalado com o provider em RAM. Um observador separado,
somente leitura, conferiu /proc/PID/exe e os mapas dos processos nos três
momentos. A existência de uma biblioteca no disco não foi usada como prova
de que ela estava carregada.

## Checks e execução

Passaram **66 verificações novas**: 27 de vínculo/delta/sintaxe e 39 do guard
das bibliotecas. Incluem boot/UUID divergentes, bool como contador, recibos
alterados, guardas históricas não aprovadas, provider com SDK/variante incorreta,
hash/modo/symlink/hardlink dos sete arquivos, diretório ausente/inseguro,
ambiente errado, operação/argumentos extras e cápsula fora de tmpfs.
Fixtures em container rootless sem rede não executam core, ROM ou bibliotecas.

O teste válido foi build/phase4/frontend-libs-session/load.o2agwm0q,
após observação observe._b95qe9h e checks checks.d8df13w5.
Menu limitado a 135 segundos, jogo com limite declarado45/runner65, retorno20
e supervisão externa240; não houve extensão das janelas nem repetição nativa.
O usuário usou A/Start/direcional/Fn+L2/Fn+Start, sem salvar.

Mapas confirmados:

    C66_MAP_MENU_FIRST_PROVIDER3_C46
    C66_MAP_GAME_PROVIDER4_INSTALLED_HOST
    C66_MAP_MENU_RETURN_PROVIDER3_C46

O host instalado saiu por hotkey, **1.732 frames**, expired0, operação0 e
cleanup0. O backend instalado fez dois status e uma exportação para RAM.
PKST/CRC/manifesto/assinaturaPNG e 26.861 bytes do core válidos; snapshot e
inventários antes/depois idênticos ao C63 e à cadeia anterior. Nenhum estado
comercial ou ROM foi coletado na prova pública.

CSV: Hz recente59,9401, cinco callbacks de underrun e1.737frames ausentes.
Esses contadores sem timestamps não localizam uma ocorrência acústica; o
usuário confirmou som limpo/audível no teste curto. Não dividir frames pelo
limite45s: houve saída voluntária. O deadline interno, áudio contínuo e
estabilidade prolongada não foram qualificados.

Foram preservados prefs55/70, mixer/DRM/brilho/volume/WirePlumber e mounts
globais. Ao final: rootRO0755, fundação97,105pré-requisitos,13arquivos instalados,
taint0, PCMclosed, p3 desmontada, UI/serviços temporários inativos, infraestrutura
PID/starttime igual e RAM removida. A página “C66 diagnostic finished” substituiu
o último frame. Host C62 e CLI C57 continuam instalados/passivos; nenhuma
biblioteca C65 foi instalada. C64 SHA671a7387 e SDK .config intactos.

## Reprodução e provas

Usar somente com as entradas históricas preservadas e estado real inspecionado:

    python3 port/scripts/prepare-phase4-frontend-libs-session.py
    python3 port/scripts/check-phase4-frontend-libs-session.py
    python3 port/scripts/run-phase4-frontend-libs-session.py --host 192.168.15.10 --boot 71 --observe

O comando observe é somente leitura no console. O runner de teste requer
--observation apontando ao stage privado, IP e boot exatos, além de checks
válidos. Não executar novamente por rotina: C66 já foi aprovado.

analyze valida o resultado técnico; finish faz a conferência final somente
leitura e a auditoria da cadeia. A confirmação física fica num recibo separado
ligado ao hash do resultado. package só congela após todos os recibos.

Prova: dist/phase4/frontend-libs-session/SHA256SUMS, fontes e metadados
sanitizados, sem imagem/ELF/ROM/estado/PNG/PCM/INI/identidade/UUID/hash da ROM.
As provas históricas e C65 permanecem intactas. Os arquivos privados contêm
recibos técnicos e observação de boot; não devem ser publicados integralmente.

O renderer é testado antes de qualquer alocação nativa. Durante o preparo,
uma primeira composição Python do trecho online acusou indentação incorreta;
foi corrigida e validada por AST/shell antes do observe/run. Não houve ensaio
físico inválido, relaxamento de checks ou correção de bibliotecas para contornar
esse erro.

## Próximo incremento

C67 proposto: receita consumidora do muxretro que declare dependência no provider
C65 e use seus hashes qualificados. Criar receita/Config.in próprios na árvore
nova, mantendo C60 e a imagem C64 históricas. Validar fonte/link/staging e
composição offline; não reinstalar componentes ou repetir o GB por rotina.
Uma mudança nos bytes do novo host exigirá qualificação própria.

A sessão manual qualifica o provider e o host instalado no novo boot observado,
sem determinar a origem desse reboot ou qualificar inicialização automática.
Frontend permanente, boot da imagem, Power/suspend, SRAM/GC, perda elétrica,
áudio contínuo e longa duração continuam separados. Nada C67 armado.

A ROM legal de GB fornecida pelo usuário basta para essa cadeia de integração.
Outros conteúdos só serão necessários ao qualificar cores de outras plataformas;
não é preciso ampliar a coleção para continuar a integração do firmware.
