from model.data_classes import ResultadoSanitizacao

def sanitizar(caminho):
    try:
        import chardet
    except ImportError:
        return ResultadoSanitizacao(False, 'Biblioteca chardet não está instalada')

    try:
        with open(caminho, 'rb') as f:
            dados = f.read()

        if not dados:
            return ResultadoSanitizacao(False, "Arquivo vazio")

        if dados.startswith(b'\xef\xbb\xbf'):
            dados = dados[3:]

        deteccao = chardet.detect(dados)
        charset_detectado = deteccao.get('encoding')
        confianca = deteccao.get('confidence', 0)

        charset_usado = None
        conteudo = None

        try:
            conteudo = dados.decode('utf-8')
            charset_usado = 'utf-8'

            padroes_double_encoding = ['Ã§', 'Ã£', 'Ã³', 'Ã¡', 'Ãª', 'Ã­', 'Ã', 'Ã©', 'Ã´', 'Ãµ', 'Ã¢']

            if any(padrao in conteudo for padrao in padroes_double_encoding):
                try:
                    conteudo_corrigido = conteudo.encode('latin-1').decode('utf-8')
                    conteudo = conteudo_corrigido
                    charset_usado = 'utf-8 (corrigido de double-encoding)'
                except(UnicodeDecodeError, UnicodeEncodeError):
                    pass

        except UnicodeDecodeError:
            if charset_detectado and confianca >= 0.7:
                charsets_fallback = [charset_detectado, 'iso-8859-1', 'windows-1252', 'cp1252']
            else:
                charsets_fallback = ['iso-8859-1', 'windows-1252', 'cp1252', 'ascii']

            for charset in charsets_fallback:
                try:
                    conteudo = dados.decode(charset)
                    charset_usado = f'convertido-de-{charset}'
                    break
                except (UnicodeDecodeError, LookupError, AttributeError):
                    continue

        if conteudo is None:
            return ResultadoSanitizacao(
                False,
                f"Falha na decodificação (detectado: {charset_detectado}, confiança: {confianca:.2f})"
            )

        return ResultadoSanitizacao(
            True, charset_usado, conteudo
        )

    except Exception as e:
        return ResultadoSanitizacao(
            False,
            f"Erro ao processar arquivo: {str(e)}"
        )

