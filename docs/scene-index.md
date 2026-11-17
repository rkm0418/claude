# 장면 번호표

게임 화면 위쪽의 `#번호`로 장면을 가리킵니다. 번호는 한번 정하면 바뀌지 않습니다(장면을 빼도 다른 번호는 그대로).

| # | 키 | 이름 | 종류 | 연결 |
|---|----|------|------|------|
| #001 | living | 거실 | house | →bedroom, →kitchen, →study, →(막힘) |
| #002 | kitchen | 주방 | house | →living |
| #003 | bedroom | 침실 | house | →living |
| #004 | study | 서재 | house | →living |
| #005 | snow_1 | 눈 숲길 1 | snow | →snow_2 |
| #006 | snow_2 | 눈 숲길 2 | snow | →snow_1, →snow_3, →snow_h |
| #007 | snow_3 | 눈 숲길 3 | snow | →snow_2, →snow_4 |
| #008 | snow_4 | 눈 숲길 4 | snow | →snow_3, →snow_5 |
| #009 | snow_5 | 눈 숲길 5 | snow | →snow_4 |
| #010 | snow_h | 눈 숲길 집 | snow | →snow_2, →tree_main |
| #011 | lake_1 | 얼음 호수 1 | lake | →lake_2 |
| #012 | lake_2 | 얼음 호수 2 | lake | →lake_1, →lake_3 |
| #013 | lake_3 | 얼음 호수 3 | lake | →lake_2, →cabin_main |
| #014 | tree_main | 나무집 안 | tree | →snow_h, →tree_back |
| #015 | tree_back | 나무집 뒷방 | tree | →tree_main, →lake_1 |
| #016 | cabin_main | 통나무집 안 | bld | →lake_3, →cabin_back, →library |
| #017 | cabin_back | 통나무집 뒷방 | bld | →cabin_main |
| #018 | library | 도서관 | bld | →cabin_main, →office |
| #019 | office | 매표소 | bld | →library, →park |
| #020 | park | 놀이공원 | world | →office, →reed |
| #021 | reed | 갈대밭 | world | →park, →woods |
| #022 | woods | 어두운 숲 | world | →reed, →ridge |
| #023 | ridge | 능선 | world | →woods, →roofs |
| #024 | roofs | 옥상 | world | →ridge, →hall |
| #025 | hall | 복도 | world | →roofs, →(막힘) |
| #026 | snowx01 | 눈 숲길 1 | wide | B→snowp01 |
| #027 | snowx02 | 눈 숲길 2 | square | B→snowp01, L→snowp02 |
| #028 | snowx03 | 눈 숲길 3 | long | L→snowp02, B→snowp03 |
| #029 | snowx04 | 눈 숲길 4 | wide | L→snowp03, B→snowp04 |
| #030 | snowp01 | 눈 숲길 통로1 | 통로 tunnel | L→snowx01, B→snowx02 |
| #031 | snowx05 | 눈 숲길 5 | deep | L→snowp04, B→snowp05 |
| #032 | snowp02 | 눈 숲길 통로2 | 통로 bend | L→snowx02, B→snowx03 |
| #033 | snowx06 | 눈 숲길 6 | deep | L→snowp05, B→snowp06 |
| #034 | snowx07 | 눈 숲길 7 | long | L→snowp06, B→snowp07 |
| #035 | snowp03 | 눈 숲길 통로3 | 통로 zig | L→snowx03, B→snowx04 |
| #036 | snowx08 | 눈 숲길 8 | square | L→snowp07, B→snowp08 |
| #037 | snowp04 | 눈 숲길 통로4 | 통로 zig | L→snowx04, B→snowx05 |
| #038 | snowx09 | 눈 숲길 9 | wide | L→snowp08, B→snowp09 |
| #039 | snowx10 | 눈 숲길 10 | square | L→snowp09, →(막힘) |
| #040 | lakex01 | 얼음 호수 1 | deep | B→lakep01 |
| #041 | lakex02 | 얼음 호수 2 | wide | L→lakep01, B→lakep02 |
| #042 | lakex03 | 얼음 호수 3 | long | L→lakep02, B→lakep03 |
| #043 | lakep01 | 얼음 호수 통로1 | 통로 zig | L→lakex01, B→lakex02 |
| #044 | lakex04 | 얼음 호수 4 | square | L→lakep03, B→lakep04 |
| #045 | lakex05 | 얼음 호수 5 | square | B→lakep04, L→lakep05 |
| #046 | lakep02 | 얼음 호수 통로2 | 통로 zig | L→lakex02, B→lakex03 |
| #047 | lakex06 | 얼음 호수 6 | wide | B→lakep05, L→lakep06 |
| #048 | lakex07 | 얼음 호수 7 | long | L→lakep06, B→lakep07 |
| #049 | lakep03 | 얼음 호수 통로3 | 통로 tunnel | L→lakex03, B→lakex04 |
| #050 | lakex08 | 얼음 호수 8 | deep | L→lakep07, B→lakep08 |
| #051 | lakep04 | 얼음 호수 통로4 | 통로 zig | L→lakex04, B→lakex05 |
| #052 | lakex09 | 얼음 호수 9 | wide | B→lakep08, L→lakep09 |
| #053 | lakex10 | 얼음 호수 10 | square | B→lakep09, →(막힘) |
| #054 | parkx01 | 폐놀이공원 1 | deep | B→parkp01 |
| #055 | parkx02 | 폐놀이공원 2 | wide | B→parkp01, L→parkp02 |
| #056 | parkp01 | 폐놀이공원 통로1 | 통로 tunnel | L→parkx01, B→parkx02 |
| #057 | parkx03 | 폐놀이공원 3 | long | L→parkp02, B→parkp03 |
| #058 | parkp02 | 폐놀이공원 통로2 | 통로 zig | L→parkx02, B→parkx03 |
| #059 | parkx04 | 폐놀이공원 4 | deep | B→parkp03, L→parkp04 |
| #060 | parkx05 | 폐놀이공원 5 | wide | B→parkp04, L→parkp05 |
| #061 | parkx06 | 폐놀이공원 6 | wide | L→parkp05, B→parkp06 |
| #062 | parkp03 | 폐놀이공원 통로3 | 통로 bend | L→parkx03, B→parkx04 |
| #063 | parkx07 | 폐놀이공원 7 | long | L→parkp06, B→parkp07 |
| #064 | parkp04 | 폐놀이공원 통로4 | 통로 bend | L→parkx04, B→parkx05 |
| #065 | parkx08 | 폐놀이공원 8 | square | L→parkp07, B→parkp08 |
| #066 | parkx09 | 폐놀이공원 9 | square | L→parkp08, B→parkp09 |
| #067 | parkx10 | 폐놀이공원 10 | square | L→parkp09, →(막힘) |
| #068 | reedx01 | 갈대밭 1 | wide | B→reedp01 |
| #069 | reedx02 | 갈대밭 2 | square | B→reedp01, L→reedp02 |
| #070 | reedp01 | 갈대밭 통로1 | 통로 bend | L→reedx01, B→reedx02 |
| #071 | reedx03 | 갈대밭 3 | long | L→reedp02, B→reedp03 |
| #072 | reedp02 | 갈대밭 통로2 | 통로 bend | L→reedx02, B→reedx03 |
| #073 | reedx04 | 갈대밭 4 | deep | B→reedp03, L→reedp04 |
| #074 | reedp03 | 갈대밭 통로3 | 통로 tunnel | L→reedx03, B→reedx04 |
| #075 | reedx05 | 갈대밭 5 | square | L→reedp04, B→reedp05 |
| #076 | reedx06 | 갈대밭 6 | deep | L→reedp05, B→reedp06 |
| #077 | reedx07 | 갈대밭 7 | long | L→reedp06, B→reedp07 |
| #078 | reedx08 | 갈대밭 8 | wide | L→reedp07, B→reedp08 |
| #079 | reedp04 | 갈대밭 통로4 | 통로 zig | L→reedx04, B→reedx05 |
| #080 | reedx09 | 갈대밭 9 | wide | L→reedp08, B→reedp09 |
| #081 | reedx10 | 갈대밭 10 | square | B→reedp09, →(막힘) |
| #082 | woodsx01 | 어두운 숲 1 | square | B→woodsp01 |
| #083 | woodsx02 | 어두운 숲 2 | square | L→woodsp01, B→woodsp02 |
| #084 | woodsp01 | 어두운 숲 통로1 | 통로 bend | L→woodsx01, B→woodsx02 |
| #085 | woodsx03 | 어두운 숲 3 | long | L→woodsp02, B→woodsp03 |
| #086 | woodsx04 | 어두운 숲 4 | square | L→woodsp03, B→woodsp04 |
| #087 | woodsx05 | 어두운 숲 5 | wide | B→woodsp04, L→woodsp05 |
| #088 | woodsp02 | 어두운 숲 통로2 | 통로 zig | L→woodsx02, B→woodsx03 |
| #089 | woodsx06 | 어두운 숲 6 | deep | B→woodsp05, L→woodsp06 |
| #090 | woodsx07 | 어두운 숲 7 | long | L→woodsp06, B→woodsp07 |
| #091 | woodsp03 | 어두운 숲 통로3 | 통로 tunnel | L→woodsx03, B→woodsx04 |
| #092 | woodsx08 | 어두운 숲 8 | deep | L→woodsp07, B→woodsp08 |
| #093 | woodsx09 | 어두운 숲 9 | wide | B→woodsp08, L→woodsp09 |
| #094 | woodsp04 | 어두운 숲 통로4 | 통로 zig | L→woodsx04, B→woodsx05 |
| #095 | woodsx10 | 어두운 숲 10 | wide | L→woodsp09, →(막힘) |
| #096 | ridgex01 | 낙엽 능선 1 | wide | B→ridgep01 |
| #097 | ridgex02 | 낙엽 능선 2 | square | L→ridgep01, B→ridgep02 |
| #098 | ridgep01 | 낙엽 능선 통로1 | 통로 bend | L→ridgex01, B→ridgex02 |
| #099 | ridgex03 | 낙엽 능선 3 | long | L→ridgep02, B→ridgep03 |
| #100 | ridgex04 | 낙엽 능선 4 | wide | B→ridgep03, L→ridgep04 |
| #101 | ridgex05 | 낙엽 능선 5 | square | B→ridgep04, L→ridgep05 |
| #102 | ridgex06 | 낙엽 능선 6 | wide | L→ridgep05, B→ridgep06 |
| #103 | ridgep02 | 낙엽 능선 통로2 | 통로 zig | L→ridgex02, B→ridgex03 |
| #104 | ridgex07 | 낙엽 능선 7 | long | L→ridgep06, B→ridgep07 |
| #105 | ridgex08 | 낙엽 능선 8 | deep | L→ridgep07, B→ridgep08 |
| #106 | ridgep03 | 낙엽 능선 통로3 | 통로 tunnel | L→ridgex03, B→ridgex04 |
| #107 | ridgex09 | 낙엽 능선 9 | square | L→ridgep08, B→ridgep09 |
| #108 | ridgep04 | 낙엽 능선 통로4 | 통로 bend | L→ridgex04, B→ridgex05 |
| #109 | ridgex10 | 낙엽 능선 10 | deep | B→ridgep09, →(막힘) |
| #110 | roofsx01 | 밤 옥상 1 | deep | B→roofsp01 |
| #111 | roofsx02 | 밤 옥상 2 | square | L→roofsp01, B→roofsp02 |
| #112 | roofsx03 | 밤 옥상 3 | long | L→roofsp02, B→roofsp03 |
| #113 | roofsp01 | 밤 옥상 통로1 | 통로 zig | L→roofsx01, B→roofsx02 |
| #114 | roofsx04 | 밤 옥상 4 | wide | B→roofsp03, L→roofsp04 |
| #115 | roofsx05 | 밤 옥상 5 | wide | B→roofsp04, L→roofsp05 |
| #116 | roofsp02 | 밤 옥상 통로2 | 통로 bend | L→roofsx02, B→roofsx03 |
| #117 | roofsx06 | 밤 옥상 6 | wide | L→roofsp05, B→roofsp06 |
| #118 | roofsp03 | 밤 옥상 통로3 | 통로 zig | L→roofsx03, B→roofsx04 |
| #119 | roofsx07 | 밤 옥상 7 | long | L→roofsp06, B→roofsp07 |
| #120 | roofsx08 | 밤 옥상 8 | square | L→roofsp07, B→roofsp08 |
| #121 | roofsp04 | 밤 옥상 통로4 | 통로 zig | L→roofsx04, B→roofsx05 |
| #122 | roofsx09 | 밤 옥상 9 | deep | L→roofsp08, B→roofsp09 |
| #123 | roofsx10 | 밤 옥상 10 | square | L→roofsp09, →(막힘) |
| #124 | hallx01 | 학교 복도 1 | deep | B→hallp01 |
| #125 | hallx02 | 학교 복도 2 | wide | B→hallp01, L→hallp02 |
| #126 | hallx03 | 학교 복도 3 | square | L→hallp02, B→hallp03 |
| #127 | hallx04 | 학교 복도 4 | square | B→hallp03, L→hallp04 |
| #128 | hallp01 | 학교 복도 통로1 | 통로 bend | L→hallx01, B→hallx02 |
| #129 | hallx05 | 학교 복도 5 | wide | L→hallp04, B→hallp05 |
| #130 | hallx06 | 학교 복도 6 | square | L→hallp05, B→hallp06 |
| #131 | hallp02 | 학교 복도 통로2 | 통로 hall | L→hallx02, B→hallx03 |
| #132 | hallx07 | 학교 복도 7 | deep | L→hallp06, B→hallp07 |
| #133 | hallx08 | 학교 복도 8 | square | L→hallp07, B→hallp08 |
| #134 | hallp03 | 학교 복도 통로3 | 통로 bend | L→hallx03, B→hallx04 |
| #135 | hallx09 | 학교 복도 9 | wide | L→hallp08, B→hallp09 |
| #136 | hallp04 | 학교 복도 통로4 | 통로 bend | L→hallx04, B→hallx05 |
| #137 | hallx10 | 학교 복도 10 | square | B→hallp09, →(막힘) |
| #138 | cabinx01 | 통나무집 1 | square | B→cabinp01 |
| #139 | cabinx02 | 통나무집 2 | deep | L→cabinp01, B→cabinp02 |
| #140 | cabinp01 | 통나무집 통로1 | 통로 hall | L→cabinx01, B→cabinx02 |
| #141 | cabinx03 | 통나무집 3 | wide | B→cabinp02, L→cabinp03 |
| #142 | cabinp02 | 통나무집 통로2 | 통로 bend | L→cabinx02, B→cabinx03 |
| #143 | cabinx04 | 통나무집 4 | square | B→cabinp03, L→cabinp04 |
| #144 | cabinp03 | 통나무집 통로3 | 통로 bend | L→cabinx03, B→cabinx04 |
| #145 | cabinx05 | 통나무집 5 | wide | L→cabinp04, B→cabinp05 |
| #146 | cabinx06 | 통나무집 6 | deep | L→cabinp05, B→cabinp06 |
| #147 | cabinx07 | 통나무집 7 | square | L→cabinp06, B→cabinp07 |
| #148 | cabinx08 | 통나무집 8 | wide | L→cabinp07, B→cabinp08 |
| #149 | cabinp04 | 통나무집 통로4 | 통로 bend | L→cabinx04, B→cabinx05 |
| #150 | cabinx09 | 통나무집 9 | square | L→cabinp08, B→cabinp09 |
| #151 | cabinx10 | 통나무집 10 | square | B→cabinp09, →(막힘) |
| #152 | libraryx01 | 도서관 1 | wide | B→libraryp01 |
| #153 | libraryx02 | 도서관 2 | square | B→libraryp01, L→libraryp02 |
| #154 | libraryp01 | 도서관 통로1 | 통로 hall | L→libraryx01, B→libraryx02 |
| #155 | libraryx03 | 도서관 3 | square | L→libraryp02, B→libraryp03 |
| #156 | libraryx04 | 도서관 4 | square | L→libraryp03, B→libraryp04 |
| #157 | libraryx05 | 도서관 5 | wide | B→libraryp04, L→libraryp05 |
| #158 | libraryp02 | 도서관 통로2 | 통로 bend | L→libraryx02, B→libraryx03 |
| #159 | libraryx06 | 도서관 6 | deep | B→libraryp05, L→libraryp06 |
| #160 | libraryp03 | 도서관 통로3 | 통로 hall | L→libraryx03, B→libraryx04 |
| #161 | libraryx07 | 도서관 7 | square | L→libraryp06, B→libraryp07 |
| #162 | libraryx08 | 도서관 8 | square | B→libraryp07, L→libraryp08 |
| #163 | libraryx09 | 도서관 9 | deep | L→libraryp08, B→libraryp09 |
| #164 | libraryp04 | 도서관 통로4 | 통로 bend | L→libraryx04, B→libraryx05 |
| #165 | libraryx10 | 도서관 10 | wide | L→libraryp09, →(막힘) |
| #166 | officex01 | 매표소 1 | wide | B→officep01 |
| #167 | officex02 | 매표소 2 | square | L→officep01, B→officep02 |
| #168 | officep01 | 매표소 통로1 | 통로 hall | L→officex01, B→officex02 |
| #169 | officex03 | 매표소 3 | deep | L→officep02, B→officep03 |
| #170 | officex04 | 매표소 4 | square | L→officep03, B→officep04 |
| #171 | officep02 | 매표소 통로2 | 통로 hall | L→officex02, B→officex03 |
| #172 | officex05 | 매표소 5 | wide | L→officep04, B→officep05 |
| #173 | officex06 | 매표소 6 | square | L→officep05, B→officep06 |
| #174 | officep03 | 매표소 통로3 | 통로 bend | L→officex03, B→officex04 |
| #175 | officex07 | 매표소 7 | square | B→officep06, L→officep07 |
| #176 | officex08 | 매표소 8 | square | L→officep07, B→officep08 |
| #177 | officex09 | 매표소 9 | deep | L→officep08, B→officep09 |
| #178 | officep04 | 매표소 통로4 | 통로 hall | L→officex04, B→officex05 |
| #179 | officex10 | 매표소 10 | wide | B→officep09, →(막힘) |
| #180 | treex01 | 나무집 속 1 | deep | B→treep01 |
| #181 | treex02 | 나무집 속 2 | square | B→treep01, L→treep02 |
| #182 | treex03 | 나무집 속 3 | wide | L→treep02, B→treep03 |
| #183 | treep01 | 나무집 속 통로1 | 통로 bend | L→treex01, B→treex02 |
| #184 | treex04 | 나무집 속 4 | wide | B→treep03, L→treep04 |
| #185 | treep02 | 나무집 속 통로2 | 통로 bend | L→treex02, B→treex03 |
| #186 | treex05 | 나무집 속 5 | wide | L→treep04, B→treep05 |
| #187 | treex06 | 나무집 속 6 | square | L→treep05, B→treep06 |
| #188 | treex07 | 나무집 속 7 | square | L→treep06, B→treep07 |
| #189 | treep03 | 나무집 속 통로3 | 통로 bend | L→treex03, B→treex04 |
| #190 | treex08 | 나무집 속 8 | square | L→treep07, B→treep08 |
| #191 | treex09 | 나무집 속 9 | square | B→treep08, L→treep09 |
| #192 | treep04 | 나무집 속 통로4 | 통로 bend | L→treex04, B→treex05 |
| #193 | treex10 | 나무집 속 10 | deep | L→treep09, →(막힘) |
| #194 | snowp05 | 눈 숲길 통로5 | 통로 zig | L→snowx05, B→snowx06 |
| #195 | snowp06 | 눈 숲길 통로6 | 통로 bend | L→snowx06, B→snowx07 |
| #196 | snowp07 | 눈 숲길 통로7 | 통로 zig | L→snowx07, B→snowx08 |
| #197 | snowp08 | 눈 숲길 통로8 | 통로 zig | L→snowx08, B→snowx09 |
| #198 | snowp09 | 눈 숲길 통로9 | 통로 bend | L→snowx09, B→snowx10 |
| #199 | lakep05 | 얼음 호수 통로5 | 통로 tunnel | L→lakex05, B→lakex06 |
| #200 | lakep06 | 얼음 호수 통로6 | 통로 zig | L→lakex06, B→lakex07 |
| #201 | lakep07 | 얼음 호수 통로7 | 통로 zig | L→lakex07, B→lakex08 |
| #202 | lakep08 | 얼음 호수 통로8 | 통로 zig | L→lakex08, B→lakex09 |
| #203 | lakep09 | 얼음 호수 통로9 | 통로 zig | L→lakex09, B→lakex10 |
| #204 | parkp05 | 폐놀이공원 통로5 | 통로 tunnel | L→parkx05, B→parkx06 |
| #205 | parkp06 | 폐놀이공원 통로6 | 통로 tunnel | L→parkx06, B→parkx07 |
| #206 | parkp07 | 폐놀이공원 통로7 | 통로 zig | L→parkx07, B→parkx08 |
| #207 | parkp08 | 폐놀이공원 통로8 | 통로 tunnel | L→parkx08, B→parkx09 |
| #208 | parkp09 | 폐놀이공원 통로9 | 통로 tunnel | L→parkx09, B→parkx10 |
| #209 | reedp05 | 갈대밭 통로5 | 통로 zig | L→reedx05, B→reedx06 |
| #210 | reedp06 | 갈대밭 통로6 | 통로 zig | L→reedx06, B→reedx07 |
| #211 | reedp07 | 갈대밭 통로7 | 통로 zig | L→reedx07, B→reedx08 |
| #212 | reedp08 | 갈대밭 통로8 | 통로 zig | L→reedx08, B→reedx09 |
| #213 | reedp09 | 갈대밭 통로9 | 통로 zig | L→reedx09, B→reedx10 |
| #214 | woodsp05 | 어두운 숲 통로5 | 통로 bend | L→woodsx05, B→woodsx06 |
| #215 | woodsp06 | 어두운 숲 통로6 | 통로 zig | L→woodsx06, B→woodsx07 |
| #216 | woodsp07 | 어두운 숲 통로7 | 통로 zig | L→woodsx07, B→woodsx08 |
| #217 | woodsp08 | 어두운 숲 통로8 | 통로 bend | L→woodsx08, B→woodsx09 |
| #218 | woodsp09 | 어두운 숲 통로9 | 통로 zig | L→woodsx09, B→woodsx10 |
| #219 | ridgep05 | 낙엽 능선 통로5 | 통로 tunnel | L→ridgex05, B→ridgex06 |
| #220 | ridgep06 | 낙엽 능선 통로6 | 통로 bend | L→ridgex06, B→ridgex07 |
| #221 | ridgep07 | 낙엽 능선 통로7 | 통로 tunnel | L→ridgex07, B→ridgex08 |
| #222 | ridgep08 | 낙엽 능선 통로8 | 통로 zig | L→ridgex08, B→ridgex09 |
| #223 | ridgep09 | 낙엽 능선 통로9 | 통로 bend | L→ridgex09, B→ridgex10 |
| #224 | roofsp05 | 밤 옥상 통로5 | 통로 tunnel | L→roofsx05, B→roofsx06 |
| #225 | roofsp06 | 밤 옥상 통로6 | 통로 tunnel | L→roofsx06, B→roofsx07 |
| #226 | roofsp07 | 밤 옥상 통로7 | 통로 tunnel | L→roofsx07, B→roofsx08 |
| #227 | roofsp08 | 밤 옥상 통로8 | 통로 zig | L→roofsx08, B→roofsx09 |
| #228 | roofsp09 | 밤 옥상 통로9 | 통로 tunnel | L→roofsx09, B→roofsx10 |
| #229 | hallp05 | 학교 복도 통로5 | 통로 hall | L→hallx05, B→hallx06 |
| #230 | hallp06 | 학교 복도 통로6 | 통로 hall | L→hallx06, B→hallx07 |
| #231 | hallp07 | 학교 복도 통로7 | 통로 hall | L→hallx07, B→hallx08 |
| #232 | hallp08 | 학교 복도 통로8 | 통로 hall | L→hallx08, B→hallx09 |
| #233 | hallp09 | 학교 복도 통로9 | 통로 hall | L→hallx09, B→hallx10 |
| #234 | cabinp05 | 통나무집 통로5 | 통로 bend | L→cabinx05, B→cabinx06 |
| #235 | cabinp06 | 통나무집 통로6 | 통로 bend | L→cabinx06, B→cabinx07 |
| #236 | cabinp07 | 통나무집 통로7 | 통로 hall | L→cabinx07, B→cabinx08 |
| #237 | cabinp08 | 통나무집 통로8 | 통로 bend | L→cabinx08, B→cabinx09 |
| #238 | cabinp09 | 통나무집 통로9 | 통로 bend | L→cabinx09, B→cabinx10 |
| #239 | libraryp05 | 도서관 통로5 | 통로 hall | L→libraryx05, B→libraryx06 |
| #240 | libraryp06 | 도서관 통로6 | 통로 hall | L→libraryx06, B→libraryx07 |
| #241 | libraryp07 | 도서관 통로7 | 통로 bend | L→libraryx07, B→libraryx08 |
| #242 | libraryp08 | 도서관 통로8 | 통로 bend | L→libraryx08, B→libraryx09 |
| #243 | libraryp09 | 도서관 통로9 | 통로 bend | L→libraryx09, B→libraryx10 |
| #244 | officep05 | 매표소 통로5 | 통로 hall | L→officex05, B→officex06 |
| #245 | officep06 | 매표소 통로6 | 통로 hall | L→officex06, B→officex07 |
| #246 | officep07 | 매표소 통로7 | 통로 hall | L→officex07, B→officex08 |
| #247 | officep08 | 매표소 통로8 | 통로 bend | L→officex08, B→officex09 |
| #248 | officep09 | 매표소 통로9 | 통로 hall | L→officex09, B→officex10 |
| #249 | treep05 | 나무집 속 통로5 | 통로 bend | L→treex05, B→treex06 |
| #250 | treep06 | 나무집 속 통로6 | 통로 hall | L→treex06, B→treex07 |
| #251 | treep07 | 나무집 속 통로7 | 통로 hall | L→treex07, B→treex08 |
| #252 | treep08 | 나무집 속 통로8 | 통로 bend | L→treex08, B→treex09 |
| #253 | treep09 | 나무집 속 통로9 | 통로 hall | L→treex09, B→treex10 |
