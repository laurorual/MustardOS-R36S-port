# C117 — perfil automático de verificações da abertura

09/11/2026, R35S Panel0, boot83/IP192.168.15.13. Usuário autorizou continuidade
e perguntou sobre autonomia dos próximos testes. Nenhum teste físico foi
solicitado nesta rodada. C116 permanece a aprovação gráfica/física anterior;
este incremento mede somente operações check, sem menu, core, botões ou áudio.

O upstream GPL3 `refs/muos/frontend/retro/core/main.c` reporta fases internas
até `Startup: ready`; esse intervalo não inclui toda a cadeia shell antes do
processo. C116 observou7,37s seleção consumida→primeiro frame, startup interno
1338,99ms e carga do conteúdo27,95ms. Não são intervalos intercambiáveis.

C117 reutiliza os scripts MIT instalados, sem modificá-los: `installed-host.sh`
em operação check verifica40arquivos e chama `frontend-libs.sh` (7bibliotecas).
Um segundo ensaio mede as7bibliotecas isoladamente. O terceiro confere o
manifesto core+ROM e faz cp/chmod400/cmp para um arquivo descartável em tmpfs.
Não executa app-launch/launch, nem copia para o caminho de conteúdo de um jogo.

As medições usam `/proc/uptime` antes/depois de cada chamada, três repetições
ordenadas, timestamps com precisão centesimal e overhead incluído. São checks
repetidos com caches aquecidos pelos guards; não há controle de frequência/cache
ou prova de tempo físicoA. Não representam coldboot nem abertura real perfilada.
Não aferem a resolução interna do relógio além da representação observada.

## Resultado nativo

`launch-profile/profile.8ov5rk96`, análise passada. Medianas e amostras em ms:

| Operação independente | Amostras | Mediana |
| --- | --- | --- |
| host_check, incluindo provider_check | 2990 /3000 /3000 | 3000 |
| provider_check isolado | 610 /610 /610 | 610 |
| hashes do conteúdo + cópia RAM | 160 /160 /150 | 160 |

Não somar host+provider: a primeira operação já contém a segunda. A leitura das
fontes C77 mostra host check no app-launch e verificação completa novamente no
launch. C117 não executa essa segunda modalidade nem mede todo o caminho gráfico.
Portanto, a dupla passagem é candidata a explicar parte da espera, sem prova de
causalidade exclusiva ou de ganho já obtido. Próximo incremento: reduzir custo
de processos/stat/hash por lote mantendo os mesmos checks de tipo, link, dono,
modo, ancestral, digest, RO e dependências; não simplesmente retirar validações.

## Integridade e escopo

17casos offline `checks.7hihu0kr`: origem C116 física/técnica/fechamento e fontes,
nove eventos/tipos/ordem/duração/completude, recusa de launch, cápsulas inválidas,
shell parsing, guard191 e adaptação finita C114 com estágio/UUID atuais.
Não usa a ROM local; o audit hook proíbe seu open. Snapshot/fontes históricas
não foram reescritos. Nenhum ELF compilado ou imagem completa criada.

O loader residente lê ROMp3 RO em namespace filho e desmonta antes da preparação
global;11assets,10scripts e metadados são conferidos antes/depois. Todos os11
recibos nativos retornaram0. Run.once permaneceu ausente, scripts e inputs
originais intactos. Infraestrutura antes/depois/pós-cleanup e mountinfo global
byte-idênticos; cápsula removida, raizRO/PCMclosed/UIoff/p1p3off. Sem escrita
persistente, novo save, reboot, uso do Deck ou acesso ao cartão original32.

Prova `dist/phase4/launch-profile`: resumo, métricas, checks e fontes; não contém
ROM/ELFs/UUID/dados privados. Não amplia a qualificação física/acústica C116.

## Autonomia dos testes

Checks de integridade, CLI/ABI, desempenho, armazenamento e encerramento
delimitados podem avançar sem supervisão física. Novo código de fluxo gráfico
pode receber validação técnica automática, mas mapas/logs/contadores não provam
ausência de flicker, distorção ou defeitos no painel/alto-falante. Solicitar
conferência física nos marcos que mudarem essas áreas, controles físicos e
energia/suspend, além de troca de cartão ou recuperação sem rede. Não repetir
os testes físicos já aprovados para mudanças que não os afetem.
