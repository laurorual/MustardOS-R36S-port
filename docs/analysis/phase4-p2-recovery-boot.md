# C89 — primeiro boot após recuperação física aprovado

Em 05/11/2026, a recuperação física da p2 e sua coleta independente foram
conferidas antes de entregar o test128 ao R35S. O helper escreveu exatamente
512 MiB; hash, releitura fria e complemento integral MBR/p1/p3 passaram.
O observador concluiu coleta e publicação, incluindo cópia independente do
novo registro C84, sem repetir a gravação. A prova dessa etapa está em
`dist/phase4/p2-recovery-native`; seu indicador de boot pendente é histórico
e permanece intacto.

O usuário devolveu o cartão ao R35S e informou IP192.168.15.10. A verificação
por SSH foi somente leitura e confirmou o primeiro contador esperado:75,
após a recuperação ter reservado74. Guardas C07/media/kernel, arquivos C76
instalados e quatro arquivos de identidade passaram. Raiz root:root0755 e
somente leitura, p3/FAT desmontadas, PCM fechado e ausência de UI ou `.once`
ativo também foram confirmados.

A política de entropia registrou `seedless`, consumo de2048bits sem crédito,
readiness antes de salvar novo seed creditável e readiness na parada. O seed
sem crédito foi consumido; o seed atual tem metadados válidos e hash diferente
dos seeds anteriores. Nenhum byte de seed foi exportado e o verificador não
carregou entropia, alterou o cartão ou solicitou reboot.

A evidência privada está em `build/phase4/recovery-boot/final-check.4y9cip12`,
pointer latest-final-check. Foram executados o render e a decodificação do
rascunho C91 com o preflight C76 existente. O main automatizado C91 ainda não
tem suite própria qualificada; esse limite não altera o resultado observado
do boot físico, mas impede tratá-lo como um coletor automatizado concluído.

Não houve novo teste de áudio/jogo: os testes físicos anteriores continuam
registrados separadamente. C79 segue sem liberação de gravação; a candidata
C88 com estado72 ficou desatualizada. O Deck ainda será necessário para essa
migração offline e mantém os backups e ferramentas. O original32 permanece
guardado. O usuário pediu encerramento por hoje; a próxima ação está no
[checkpoint](phase4-resume-checkpoint.md).
