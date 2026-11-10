# C84 — contrato de recuperação pósboot testado offline

Concluído em **04/11/2026**. Implementados o contrato de recuperação, o registro
durável de possível tentativa de boot e a composição dos payloads privados.
**Ainda não há coletor pósboot de produção, compositor de imagem de produção
ou backend de recuperação física.** A migração C79 continua bloqueada por esses
componentes; este resultado não autoriza tratá-la como pronta para gravar.

Uma consulta somente leitura confirmou o Deck Jupiter/IP192.168.15.13 com
test128 desmontado, quatro aliases kernelRO e regra temporária C83 presente.
Depois disso, todo preparo/teste foi local, sem SSH ou IO no cartão. Não houve
seed novo para o dispositivo, chave nova, fence real, provisionamento, reboot
ou troca de mídia. Original32 fora do fluxo; SDK e imagens anteriores intactos.

## Problema e escolha

Restaurar a p2 byte a byte depois de uma possível inicialização pode repetir
um seed já creditado e recuar o contador. A regra C80 permanece estrita: falta
de rede ou tela apagada não prova que o kernel/init não iniciou. O contrato
separa a intenção persistida antes da entrega da mídia da captura offline
posterior. Nenhuma evidência JSON isolada autentica um dispositivo ou autoriza
IO: o futuro controller terá de derivá-la de descritores e cópias verificados.

Não foi alterado código upstream. Foram consultados o fluxo nativo C07 em
`network-diagnostic/run.sh`, a política `entropy-diagnostic/functions.sh` e
o contrato C80. A implementação nova em Python é MIT. A política de entropia
extraída somente para leitura da raiz regular C79 coincide por hash com a fonte
exercitada nos testes; nenhum init ou SeedRNG da imagem foi executado.

## Implementação

| Componente | Responsabilidade |
| --- | --- |
| `phase4_root_recovery.py` | Contrato puro, reserva de contador, payload, fence e leitura pinada |
| `check-phase4-root-recovery.py` | Guardas, falhas de RNG/fsync e leitura de fence |
| `phase4-root-recovery-fixture.py` | Ext4 sintética real e política de entropia com stubs |
| `prepare-phase4-root-recovery.py` | Conferência offline das provas e vínculo privado C82/C83 |
| `package-phase4-root-recovery.py` | Congelamento de fontes e resultado público sem privados |

Antes de entregar uma futura candidata ao console, `attempt_record()` descreve
`BOOT_MAY_HAVE_OCCURRED`, identificador único, hash da candidata, backup e piso
do contador. `seal_attempt()` cria folha exclusiva0400 em diário privado0700,
sincroniza arquivo e diretório e só então retorna sucesso. Fence existente ou
parcial não é sobrescrito/rearmado. Falha de fsync retém a parcial e impede o
sinal de sucesso para entrega. `load_attempt()` exige hash esperado, owner,
modo, link único, regularidade e conteúdo canônico estável. Não é assinatura
contra um usuário capaz de modificar o diário; o controller precisa conferir
também o vínculo com o backup. Nenhuma função cancela a possibilidade de boot.

Para recuperar depois de uma tentativa, exige captura offline nova vinculada
ao mesmo fence/cartão, fsck0, raiz0755, contador legível e manifesto privado.
Recusa fonte suja/ilegível, contador abaixo do piso e identidade de rede/key
alterada, inclusive desaparecimento do auxiliar público opcional. A presença
dos seeds atuais pode ser zero, um ou ambos: o boot pode tê-los consumido antes
de falhar. Entradas privadas desconhecidas e metadados permissivos abortam.

O novo contador é `max(backup, piso da entrega, observação posterior) + 1`.
Reserva um valor e deixa o C07 incrementar novamente no boot seguinte. Exemplo
sintético: backup72, piso72 e observação75 produzem recuperação76 e próximo
C07=77. Mesmo observação72 após falha precoce reserva73. Recusa saturação que
não deixaria o próximo boot dentro do limite9999. Isso mantém monotonicidade
em relação às observações duráveis conhecidas; não é um contador resistente
a adulteração ou garantia de registrar boots perdidos em queda elétrica.
Sem contador confiável não há fallback para o valor antigo do backup.

Payload preserva exatamente auth/config/host key e auxiliar público. Remove
ambos os caminhos antigos de seed; inclui apenas `seed.no-credit` novo256bytes
em0400, contador0600 e diretórios privados0700. Raiz alvo0755 normaliza o modo
0777 histórico da cópia C82 sem reescrever essa cópia. O gerador usa somente
`getrandom(256, GRND_NONBLOCK)` do host já pronto: EAGAIN, EINTR, ENOSYS,
resposta curta ou hash igual a seed conhecido abortam sem fallback/retry.
Não há carga no RNG, crédito de entropia, geração de chave ou execução de init.

A política nativa, diante de ausência de `seed.credit`, aguarda readiness antes
de chamar SeedRNG para consumir `seed.no-credit` sem crédito. Pode esperar ou
falhar no aparelho sem entropia suficiente: a recuperação não mascara essa
limitação relabelando bytes como creditáveis. O teste não credita nada no kernel
do host/container: readiness e o executável SeedRNG são stubs explícitos.

## Verificações e vínculo real

**85casos passaram**, incluindo identidade/capacidade/fence, tipos/owners/modos,
contador/hash/limites, sementes ausentes, mudança de identidade, RNG falho sem
retry, colisão com seed antigo, fsync do arquivo/diretório, fence parcial,
symlink/hardlink e fonte modificada. Um primeiro caso de diretório permissivo
foi corrigido no teste: umask077 estava tornando sua fixture0700. Nenhum
problema no cartão motivou essa correção.

Em container existente sem rede/dispositivos/capabilities, três ext4 regulares
sintéticas32MiB representaram backup0777, captura posterior0755/contador75 sem
seeds e recuperação0755/contador76. Fsck sem reparo passou; inventário lógico
integral da árvore pública e identidade de rede ficou igual, os dois seeds
antigos foram removidos e o seed novo ficou0400. O backup regular permaneceu
byte-idêntico. Um teste adicional executou a biblioteca de entropia real com
stubs: confirmou probes0/60, espera de readiness e consumo sem crédito. Não é
ensaio de boot, IO físico ou atomicidade da flash.

O preparo real verificou novamente hashes/tamanhos de todos os artefatos C82,
seis privados, quatro folhas de identidade estável e contador72, vinculados
à conclusão C83. Provas ancestrais e raiz extraída C79 também conferidas.
Nenhuma cópia C82/C83 foi normalizada ou editada. Como não houve tentativa da
candidata provisionada, não foi inventada captura pósboot nem criado fence
real, seed novo ou imagem de recuperação para o cartão atual.

Privados em `build/phase4/root-recovery`: checks `checks.rmpbaxzl`, preparo
`readiness.cpx2y971`; pointers `latest-checks` e `latest-readiness`. Somente
fontes, casos sintéticos e resumo redigido entram em `dist/phase4/root-recovery`.
Não publicar binding/manifestos reais, seeds, chaves, ROM, hashes privados ou
imagens ext4. As fixtures pequenas ficam no build ignorado, sem rebuild de SDK.

## Próximo incremento

C85 deve fornecer compositor de imagem **regular** e coletor pósboot limitado,
com leitura de fonte e árvore pública efetivamente verificada, preparação sem
execução de init e recibos derivados do IO. Depois qualificar backend p2-only
e fence antes de transferir a mídia. O backend não pode limpar kernelRO ou
trocar guardas C83 implicitamente; mudança de proteção precisa de etapa própria
planejada. Não reutilizar restore C20 nem generalizar escrita na p3. Manter o
cartão no Deck e adiar testes físicos até existir mudança concreta testável.
