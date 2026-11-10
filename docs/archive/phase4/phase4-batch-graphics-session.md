# C121 — qualificação gráfica do contrato de execução em lote

09/11/2026, R35S Panel0, boot84/IP192.168.15.15. O novo boot foi observado
explicitamente antes do teste; as observações/provas dos boots anteriores
permanecem intactas. Instalações C112/C113 e importação da ROM não foram
repetidas. O cartão original32 e o Steam Deck ficaram fora do fluxo.

## Fluxo e contratos

O entrypoint C121 usa os quatro nomes corretos do provider e exige análise,
prova e bundle C120 exatos. A cápsula é preparada pelo loader residente,
com ROM interna p3 e onze assets locais. Somente seis arquivos de código e
metadados do contrato são enviados à RAM; não há leitura da ROM no host nem
uploads de ROM/ELFs/assets.

A adoção cria backup e stage próprios, reserva o run.once antigo antes de
trocar o host da cápsula e preserva metadados antigos. Run válido cria outra
reserva antes de executar o subreaper240s e o worker instalado original,
no namespace privado, com filho210s/jogo45s. O provider, os outros scripts e
o pacote instalado C105 não são substituídos. A mudança em lote cobre somente
a validação do host; todos os checks de conteúdo e a restauração load-only
continuam no caminho original.

O fluxo de preparação/execução/retorno upstream foi conferido em
`internal/script/mux/frontend.sh` e `launch.sh`, sem copiar ou alterar essas
referências. O código original do port reutilizado é MIT. Não houve mudança
ABI, recompilação de ELF, imagem nova ou autostart.

## Registros da rodada

Observação atual: `batch-graphics/observe.g0k9zci0`, guard191 e boot/UUID/infra
aprovados. Sessão: `load.0hrtc9t5`, criada em cápsula nova. O watcher confirmou
o worker instalado e o primeiro menu antes de solicitar A/Start/direcional/
Fn+L2/Fn+Start ao usuário. Os oito checks offline C121 já aprovados não foram
repetidos sem mudança de fontes.

**APROVADO:** operação0/cleanup0,1134frames; watcher confirmou os três mapas
e cmdline do worker instalado. O host C120 foi usado no launch e o provider
permaneceu original. A reserva nova e a reserva antiga, hashes/modos do bundle,
worker e metadados anteriores foram conferidos após a execução.

O usuário confirmou imagem/direcional/som limpo e audível, restauração com
Fn+L2 e saída/retorno por Fn+Start: “Tudo certo. A velocidade para abrir o
jogo melhorou um pouco.” A observação física e a análise técnica referem-se
ao mesmo digest de análise da sessão. Snapshot/inventários C63 e metadados
permaneceram byte-idênticos; nenhum save novo foi solicitado ou registrado.

Analisador e finisher C121 executados sobre os recibos reais passaram.
Infraestrutura antes/depois idêntica, montagens globais preservadas, todos
os recibos de cleanup/saúde0, RAM removida e tela final diagnóstica escrita.
RaizRO0755/PCMclosed/UIoff/p1p3off/taint0; preferências55/70 e restaurações de
mixer/DRM/WirePlumber preservadas. Imagem C64, SDK e provas ancestrais íntegros.

| Medição | Resultado |
| --- | --- |
| Seleção consumida → primeiro frame observado | 4,27s |
| Startup interno reportado pelo core | 1369,42ms |
| Frequência recente reportada | 59,8802Hz |
| Frame médio | 16,6834ms |
| Áudio: underruns / frames ausentes | 4 /1971 |

O C116 registrou7,37s para o intervalo observado; nesta rodada ele ficou
menor e o usuário percebeu melhora. A comparação não tem controle de
frequência, cache, estado do boot ou atraso do watcher; não atribuir toda a
diferença ao lote nem apresentar percentual garantido de aceleração.
Os underruns permanecem registrados, apesar da confirmação acústica positiva;
não equivalem a áudio sem perdas nem qualificam estabilidade longa.

## Publicação e limites

O publicador próprio exige análise nativa, análise técnica, observação física
e fechamento aprovados e vinculados à mesma sessão, mais os recibos reais do
novo caller/worker e C120. Recusa publicação prematura; não publica ROM, ELF,
UUID, seed, identidade privada ou snapshot. Provas e fontes anteriores ficam
congeladas. A publicação prematura foi recusada em
`publication-check.zdr0ymc2`, com saída não zero e nenhuma prova criada. A
prova final qualificada é `dist/phase4/batch-graphics`, com resumo/checks/
métricas/fontes sanitizados. O contrato/pacote instalado continua C105; o host
otimizado foi qualificado em RAM, sem instalação persistente nesta rodada.

O intervalo seleção consumida → primeiro frame usa amostragem nominal de1s,
sem limite comprovado de atraso do watcher nem timestamp físico do botão.
Uma rodada não constitui benchmark estatístico da abertura, estabilidade longa,
qualificação de energia/suspend ou navegador geral de ROMs.
