# C111 — callback final do preparador

Data: 07/11/2026. Revisão da integração C109 antes de abrir qualquer UI.
Além dos modos corrigidos no C110, o callback final que reutiliza funções
C105 precisa atender caller_exec capsule: c105_staged primeiro confere o
tmpfs por c105_capsule. O callback original só tratava boot; a fixture C107
mockava esse dispatch e não cobria a entrada instalada. A revisão adiciona
a conferência findmnt de tmpfs, sem relaxar os checks C105 ou modos locais.

C107/C108/C110 permanecem congelados. A instalação aditiva usa um terceiro
prefixo próprio, `/usr/libexec/muos-capsule-v3`, com seis arquivos pequenos.
Nenhum arquivo anterior é substituído. Três revisões de scripts desta rodada
somam cerca de31KiB; não são três imagens de firmware. As versões iniciais
ficam como regressão explícita e não recebem aprovação de preparo gráfico.

O teste novo executa o callback extraído da entrada gerada, com funções C105
reais e tmpfs real no container. Somente os caminhos de fixture e o conteúdo
boot/UUID são ajustados; o dispatch capsule e os metadados não são mockados.
Mantém a regressão do modo0644 e os casos anteriores de prepare/rollback.
O instalador confere172 arquivos existentes antes de adicionar o pacote;
claim único, fingerprint privado e retorno RO permanecem obrigatórios.

44 casos passaram em `capsule-prepare-v3/checks.21y_q3b5`.
Instalação concluída em `capsule-prepare-v3/install.enw93t77`, boot81:
seis arquivos/10.602bytes, nenhuma substituição. Check/recusa vazia/fechamento
nativos0, fingerprint privado/infraestrutura/montagens preservados, RAM
removida, raizRO. Claim consumido; não repetir apply. Nenhum jogo, ROM, save,
reboot ou UI foi executado pela instalação. A prova é
`dist/phase4/capsule-preparer-v3-installed`.

C109 só poderá afirmar aprovação gráfica após seus21 checks de roteamento,
um preparo positivo real e a sessão menu→jogo→menu com confirmação física.
Guardas da integração cobrem178 arquivos, incluindo os três prefixos.
