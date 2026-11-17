#!/usr/bin/env python3
"""두 시선 퍼즐(설계 문서 §31): 방마다 같은 사물을 아이의 눈(child)으로 한 번, 바깥의 눈(adult)으로 한 번 푼다. 글 없음.
export_web.py 가 방 데이터에 views 로 붙인다. 좌표는 각 방의 바닥 좌표(x, d), z 는 높이."""
def O(id, kind, x, d, z=0, **kw): return dict(id=id, kind=kind, x=x, d=d, z=z, **kw)
T940, TRAP = [9, 40], [2, 15]
VIEWS = {
    'tree_main': dict(flag='tm', views=[
        dict(mode='child', objects=[                                              # 1 멈춘 시계: 셋은 9시 40분에 멈췄고 자명종만 간다. 상자 눈금 9·4·0
            O('tm_c1', 'look', 30, 58, 34, look='clock', time=T940, reach=30, h=10), O('tm_c2', 'look', 86, 52, 37, look='clock', time=T940, reach=30, h=10), O('tm_c3', 'look', 30, 10, 11, look='clock', time=T940, reach=30, h=10),
            O('tm_c4', 'look', 17, 46, 16, look='clock', time=TRAP, tick=True, reach=30, h=10),
            O('tm_d1', 'dial', 44, 33, 13, n=10, want=9, look='num', reach=26, h=8), O('tm_d2', 'dial', 50, 33, 13, n=10, want=4, look='num', reach=26, h=8), O('tm_d3', 'dial', 56, 33, 13, n=10, want=0, look='num', reach=26, h=8)], box=[42, 58, 33, 13]),
        dict(mode='adult', give='cup_s', kid=[20, 40], objects=[                 # 2 건전지: 시계 뒤 자리에 맞는 크기의 건전지를 끼운다
            O('tm_b', 'slot', 30, 58, 30, n=4, want=1, init=-1, look='battery', reach=30, h=10), O('tm_k', 'look', 30, 58, 40, look='clock', time=T940, reach=30, h=8)]),
    ]),
    'tree_back': dict(flag='tree_open', req='tm', views=[
        dict(mode='child', kid=None, beam=dict(kind='block', frm=[52, 48, 38], to=[20, 12, 4], via=['tb_a', 'tb_b', 'tb_c'], trap='tb_x'), objects=[   # 3 숨기: 상자를 밀어 창의 빛을 가린다(하나는 밀면 오히려 틈이 난다)
            O('tb_a', 'toggle', 44, 34, 0, n=2, want=1, look='crate', shift=[-4, -8], reach=18, h=12), O('tb_b', 'toggle', 38, 20, 0, n=2, want=1, look='crate', shift=[-3, 6], reach=18, h=12),
            O('tb_c', 'toggle', 22, 22, 0, n=2, want=1, look='crate', shift=[6, -4], reach=18, h=12), O('tb_x', 'toggle', 30, 28, 0, n=2, want=0, look='crate', shift=[10, 2], init=0, reach=18, h=12)]),
        dict(mode='adult', kid=[20, 12], trail=[[56, 22], [48, 26], [44, 31], [40, 24], [34, 20], [28, 20], [24, 18]], seq=['tb_p1', 'tb_p2', 'tb_p3'], objects=[   # 4 찾기: 작은 발자국을 따라 상자를 차례로 치운다
            O('tb_p1', 'press', 44, 31, 0, look='crate', reach=18, h=12), O('tb_p2', 'press', 34, 20, 0, look='crate', reach=18, h=12), O('tb_p3', 'press', 24, 16, 0, look='crate', reach=18, h=12), O('tb_p4', 'press', 34, 8, 0, look='crate', reach=18, h=12)]),
    ]),
    'cabin_main': dict(flag='cm', views=[
        dict(mode='child', seq=['cm_b1', 'cm_b0', 'cm_b2', 'cm_b1'], gate='cm_heard', objects=[   # 5 따라 치기: 라디오의 네 음을 종 셋으로
            O('cm_r', 'play', 30, 18, 0, look='radio', notes=[1, 0, 2, 1], bells=['cm_b0', 'cm_b1', 'cm_b2'], sets='cm_heard', reach=18, h=12),
            O('cm_b0', 'press', 30, 34, 30, look='bell', tone=0, size=5, reach=20, h=10), O('cm_b1', 'press', 44, 34, 32, look='bell', tone=1, size=4, reach=20, h=10), O('cm_b2', 'press', 56, 40, 34, look='bell', tone=2, size=3, reach=20, h=10)]),
        dict(mode='adult', give='cup_m', kid=[86, 36], wave=dict(ids=['cm_f', 'cm_v'], at=[30, 18, 22]), objects=[   # 6 주파수: 눈금 둘을 돌려 잡음을 걷어 낸다
            O('cm_f', 'dial', 27, 18, 6, n=6, want=4, look='knob', reach=20, h=8), O('cm_v', 'dial', 33, 18, 6, n=6, want=2, look='knob', reach=20, h=8), O('cm_rr', 'look', 30, 18, 0, look='radio', reach=0, h=1)]),
    ]),
    'cabin_back': dict(flag='cabin_key', req='cm', views=[
        dict(mode='child', shadows=dict(lamp='cb_l', at=[[58, 18], [56, 24], [59, 27]]), objects=[   # 7 문 앞의 것: 등불 자리를 옮겨 문틈의 그림자를 지운다
            O('cb_l', 'dial', 40, 22, 0, n=3, want=2, look='lamp', pos=[[40, 22], [30, 12], [50, 16]], reach=20, h=14)]),
        dict(mode='adult', kid=[12, 30], objects=[                                # 8 밥상: 쟁반의 패인 자리에 그릇·수저·컵
            O('cb_s0', 'slot', 44, 20, 3, n=3, want=2, init=-1, look='piece', reach=18, h=6), O('cb_s1', 'slot', 50, 20, 3, n=3, want=0, init=-1, look='piece', reach=18, h=6), O('cb_s2', 'slot', 47, 26, 3, n=3, want=1, init=-1, look='piece', reach=18, h=6)], tray=[41, 53, 17, 29]),
    ]),
    'library': dict(flag='lib_open', views=[
        dict(mode='child', kid=[56, 20], beam=dict(kind='cut', to=[56, 20, 8], via=['lb_f0', 'lb_f1', 'lb_f2']), objects=[   # 9 눈을 가린다: 세워진 액자를 엎어 빛을 끊는다
            O('lb_f0', 'toggle', 15, 17, 12, n=2, want=1, look='frame', reach=20, h=8), O('lb_f1', 'toggle', 15, 47, 12, n=2, want=1, look='frame', reach=20, h=8), O('lb_f2', 'toggle', 97, 27, 12, n=2, want=1, look='frame', reach=20, h=8)]),
        dict(mode='adult', give='cup_l', kid=[56, 20], beam=dict(kind='link', frm=[0, 32, 30], to=[94, 62, 20], via=['lb_g0', 'lb_g1', 'lb_g2']), objects=[   # 10 다시 세운다: 액자를 세우고 방향을 맞춰 창의 빛을 문까지
            O('lb_g0', 'toggle', 15, 47, 12, n=3, want=2, init=0, look='frame3', reach=20, h=8), O('lb_g1', 'toggle', 15, 17, 12, n=3, want=1, init=0, look='frame3', reach=20, h=8), O('lb_g2', 'toggle', 97, 27, 12, n=3, want=2, init=0, look='frame3', reach=20, h=8)]),
    ]),
    'office': dict(flag='office_open', views=[
        dict(mode='child', seq=['of_c2', 'of_c0', 'of_c1'], stack=[45, 6], objects=[   # 11 문을 막는다: 의자 셋을 큰 것부터 문 앞에 쌓는다
            O('of_c0', 'press', 22, 30, 0, look='chair', size=1, reach=18, h=12), O('of_c1', 'press', 70, 32, 0, look='chair', size=0, reach=18, h=12), O('of_c2', 'press', 46, 24, 0, look='chair', size=2, reach=18, h=12)]),
        dict(mode='adult', kid=[45, 14], knock=[3, 2], objects=[O('of_k', 'knock', 45, 3, 14, look='door', reach=22, h=22)]),   # 12 문 밖: 안에서 들리던 박자 그대로 두드린다(셋, 쉬고, 둘)
        dict(mode='both', objects=[                                               # 13 세 자리: 컵 셋을 창턱의 물 자국 크기에 맞춘다
            O('of_s0', 'slot', 20, 45, 18, n=3, want=2, init=-1, look='cup', reach=26, h=8), O('of_s1', 'slot', 33, 45, 18, n=3, want=0, init=-1, look='cup', reach=26, h=8), O('of_s2', 'slot', 46, 45, 18, n=3, want=1, init=-1, look='cup', reach=26, h=8)]),
    ]),
}
