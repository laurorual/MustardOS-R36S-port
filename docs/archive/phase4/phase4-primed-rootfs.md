# C38 — composição privada com prime PCM

O composer foi atualizado para consumir C36 e recusar execução antes de provas
positivas e imutáveis do bootC37 e seu fallback. As provas devem vincular o mesmo
plano instalado, som físico aprovado, acessoRW e prime PCM. Esse gate impede que
uma sessão quente ou apenas metadados sejam promovidos como correção de boot.

O perfil é selecionado pelo manifesto do candidatoC36 aprovado, pois a atualização
de dois arquivos não contém uma nova linha de perfil. S95 e WirePlumber precisam
coincidir com o alvo instalado; a composição aplica ambos antes de gerar a
fundação97. Além dos hashes, preserva a ordem do manifesto nativo. Os dez arquivos
centrais (fundação, payloads, perfil/certificado, inittab, S95 e políticaRW) devem
ser byte-idênticos ao candidato instalado, antes e após releitura da imagem.

Imagem ext4ROOTFS512MiB permanece privada em build/. Factorycounter0/0600 em
pasta0700, C07/defaultsoff, sem.once/recibos usados, seed, chavesSSH ou credenciais.
Isso nunca autoriza resetar contador/privados ou gravar a imagem na raiz viva.
A imagemC27/96 anterior é preservada. A composição reaproveita a baseC07 e ELFs
já auditados; não é um rebuild completo do Buildroot ou uma prova de boot da
imagem inteira. Redistribuição de blobsGPU segue pendente.

Verificação prevista: macros de instalação, contrato de boot antes/depois,
fsck offline/readback integral, inventário estático/ABI, loaders QEMU, fixtures
com hashes recalculados que removem prime/RW e equivalênciaC36. Provas públicas
excluem a imagem, blobs, raw áudio e privados. Consulte Estado atual do checkpoint
para saber se a execução terminou; não confundir fonte preparada com imagem pronta.

## Composição executada

Stage privado `build/phase4/rootfs-candidate/composition.w59vz7vo`,
experimentoC38, ext4ROOTFS536870912bytes. SHA256
`7b2718beec0aa75fd5b6d81570c9e98857efa00f01638d7f04159a73d711320d`.
Fsck offline, releitura integral e root0755 passaram;305ELF userspace e555módulos
AArch64 auditados,172loaders QEMU passaram. Fundação97 e dez arquivos nativos
coincidem byte-exato comC36. SDK/base preservados; imagemC27 anterior conservou
SHA6977d8174ec2e89f0f1a4964f1ee533d7720acd47e28b231151ed478534af826.
28fixtures finais passaram, incluindo remoção de prime/RW com hashes
recalculados. Provas públicas em `dist/phase4/rootfs-pcm-primed`; imagem privada
não incluída. Não gravar esta imagem na raiz viva. Nenhum boot desta imagem inteira foi realizado.
