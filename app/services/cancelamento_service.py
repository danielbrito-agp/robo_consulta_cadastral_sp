
'''
Esta def é responsável por cancelar o pedido no banco C5, caso o cliente não esteja habilitado na SEFAZ.

'''

def cancelar_pedido(cursor, nro_pedido, nro_empresa):

    cursor.execute("""
    begin
      consinco.sp_cancela_pedvenda(
        pnnropedvenda => :1,
        pnnroempresa => :2,
        psusucancelamento => :3,
        psmotcancelamento => :4,
        psobspedido => :5
      );
    end;
    """, [
        nro_pedido,
        nro_empresa,
        "ROBO_SEFAZ",
        "CNPJ NÃO HABILITADO NA SEFAZ",
        "Cancelamento automático"
    ])