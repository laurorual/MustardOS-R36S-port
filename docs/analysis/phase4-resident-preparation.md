# C114 — preparação automática com ROM interna, sem UI

Concluído em07/11/2026, boot82/IP192.168.15.8. Usuário ausente; não foi aberta
sessão que exigisse botões ou avaliação visual/acústica. C112/C113 aprovados
são pré-requisitos, com fontes/provas/recibos e backup independente conferidos.

`resident-preparation/validate.5l2corol` usou apenas comandos SSH. Nenhum asset
ou ROM foi enviado para a cápsula. Um audit hook Python recusa open de qualquer
caminho `/port/roms/`; a validação passou com essa proibição ativa. Lê o digest
privado já conferido na importação C113 e os manifestos públicos históricos.
Portanto, o conteúdo da ROM local não é entrada deste teste.

`load.sh prepare` residente copiou quatro assets locais, montou p3 RO/noload em
namespace privado, conferiu o shelf C113 e copiou ROM para RAM. Desmontou/removeu
o mountpoint antes de voltar ao namespace global e chamar C111. C111 gerou
identidade/metadados, copiou mais sete bibliotecas locais e usou stage C105 para
os dez scripts. Marcas C105/C111/C112 conferidas; run.once AUSENTE. Nenhum worker,
menu, core de jogo, áudio, input ou reboot foi executado.

Foram conferidos11assets públicos RAM e dez scripts, hashes/modos/donos/nlink e
comparação dos scripts com a instalação. ROM64KiB coincide com o digest privado
C113/C109. Identidade, roleload, manifesto GB/core/ROM e os três manifestos de
scripts são byte-exatos; metadados0600, ROM/assets/scripts700, boot/UUID do stage
atuais. Raiz191hashes, layout e guard c25_ready integral preservados.

CLI instalada de host passou; probe eager nativo carregou as quatro bibliotecas
com símbolos esperados, e muxretro --version/--help passaram. Esses comandos
não iniciam o render/core de jogo. Não substituem a futura validação física de
imagem, controles, restauração e áudio no boot82.

Todos os recibos nativos0; infraestrutura PID/starttime e mountinfo global
idênticos antes/depois, p3 desmontada, raizRO0755/PCMclosed/UIoff/taint0.
Cápsula RAM removida e preferências/estado persistentes não escritos. Fonte e
prova C109, SDK e imagens de regressão não foram alterados. Prova sanitizada
`dist/phase4/resident-preparation`, sem ELF/ROM/seed/snapshot/backup/UUID.

A integração gráfica C115 ficará pronta e testada offline para uma rodada
supervisionada posterior. Até essa rodada, não classificar o fluxo gráfico
com ROM interna como aprovado e não publicar prova física sintética.
