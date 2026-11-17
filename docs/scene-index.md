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
| #026 | snowx01 | 눈 숲길 1 | wide | F→snowx02 |
| #027 | snowx02 | 눈 숲길 2 | deep | B→snowx01, R→snowx03 |
| #028 | snowx03 | 눈 숲길 3 | long | L→snowx02, R→snowx04 |
| #029 | snowx04 | 눈 숲길 4 | square | L→snowx03, R→snowp01 |
| #030 | snowp01 | 눈 숲길 통로1 | 통로 zig | L→snowx04, R→snowx05(이어붙이기) |
| #031 | snowx05 | 눈 숲길 5 | deep | L→snowp01(이어붙이기), B→snowp02 |
| #032 | snowp02 | 눈 숲길 통로2 | 통로 bend | F→snowx05, R→snowx06 |
| #033 | snowx06 | 눈 숲길 6 | square | L→snowp02, R→snowx07(이어붙이기) |
| #034 | snowx07 | 눈 숲길 7 | long | L→snowx06(이어붙이기), R→snowp03 |
| #035 | snowp03 | 눈 숲길 통로3 | 통로 tunnel | L→snowx07, R→snowx08 |
| #036 | snowx08 | 눈 숲길 8 | square | L→snowp03, F→snowp04(이어붙이기) |
| #037 | snowp04 | 눈 숲길 통로4 | 통로 bend | B→snowx08(이어붙이기), R→snowx09(이어붙이기) |
| #038 | snowx09 | 눈 숲길 9 | wide | L→snowp04(이어붙이기), R→snowx10 |
| #039 | snowx10 | 눈 숲길 10 | wide | L→snowx09, →(막힘) |
| #040 | lakex01 | 얼음 호수 1 | deep | B→lakex02(이어붙이기) |
| #041 | lakex02 | 얼음 호수 2 | square | F→lakex01(이어붙이기), R→lakex03 |
| #042 | lakex03 | 얼음 호수 3 | long | L→lakex02, R→lakep01 |
| #043 | lakep01 | 얼음 호수 통로1 | 통로 zig | L→lakex03, R→lakex04(이어붙이기) |
| #044 | lakex04 | 얼음 호수 4 | wide | L→lakep01(이어붙이기), B→lakex05(이어붙이기) |
| #045 | lakex05 | 얼음 호수 5 | wide | F→lakex04(이어붙이기), R→lakep02(이어붙이기) |
| #046 | lakep02 | 얼음 호수 통로2 | 통로 bend | L→lakex05(이어붙이기), F→lakex06(이어붙이기) |
| #047 | lakex06 | 얼음 호수 6 | square | B→lakep02(이어붙이기), R→lakex07(이어붙이기) |
| #048 | lakex07 | 얼음 호수 7 | long | L→lakex06(이어붙이기), R→lakep03(이어붙이기) |
| #049 | lakep03 | 얼음 호수 통로3 | 통로 tunnel | L→lakex07(이어붙이기), R→lakex08 |
| #050 | lakex08 | 얼음 호수 8 | deep | L→lakep03, B→lakep04(이어붙이기) |
| #051 | lakep04 | 얼음 호수 통로4 | 통로 bend | F→lakex08(이어붙이기), R→lakex09 |
| #052 | lakex09 | 얼음 호수 9 | wide | L→lakep04, B→lakex10 |
| #053 | lakex10 | 얼음 호수 10 | square | F→lakex09, →(막힘) |
| #054 | parkx01 | 폐놀이공원 1 | square | B→parkx02 |
| #055 | parkx02 | 폐놀이공원 2 | square | F→parkx01, R→parkp01(이어붙이기) |
| #056 | parkp01 | 폐놀이공원 통로1 | 통로 tunnel | L→parkx02(이어붙이기), R→parkx03 |
| #057 | parkx03 | 폐놀이공원 3 | long | L→parkp01, R→parkp02 |
| #058 | parkp02 | 폐놀이공원 통로2 | 통로 tunnel | L→parkx03, R→parkx04(이어붙이기) |
| #059 | parkx04 | 폐놀이공원 4 | deep | L→parkp02(이어붙이기), B→parkx05 |
| #060 | parkx05 | 폐놀이공원 5 | square | F→parkx04, B→parkx06(이어붙이기) |
| #061 | parkx06 | 폐놀이공원 6 | wide | F→parkx05(이어붙이기), R→parkp03(이어붙이기) |
| #062 | parkp03 | 폐놀이공원 통로3 | 통로 zig | L→parkx06(이어붙이기), R→parkx07 |
| #063 | parkx07 | 폐놀이공원 7 | long | L→parkp03, R→parkp04 |
| #064 | parkp04 | 폐놀이공원 통로4 | 통로 bend | L→parkx07, B→parkx08 |
| #065 | parkx08 | 폐놀이공원 8 | deep | F→parkp04, B→parkx09(이어붙이기) |
| #066 | parkx09 | 폐놀이공원 9 | wide | F→parkx08(이어붙이기), B→parkx10 |
| #067 | parkx10 | 폐놀이공원 10 | wide | F→parkx09, →(막힘) |
| #068 | reedx01 | 갈대밭 1 | square | B→reedx02(이어붙이기) |
| #069 | reedx02 | 갈대밭 2 | square | F→reedx01(이어붙이기), R→reedp01(이어붙이기) |
| #070 | reedp01 | 갈대밭 통로1 | 통로 zig | L→reedx02(이어붙이기), R→reedx03 |
| #071 | reedx03 | 갈대밭 3 | long | L→reedp01, R→reedp02(이어붙이기) |
| #072 | reedp02 | 갈대밭 통로2 | 통로 tunnel | L→reedx03(이어붙이기), R→reedx04(이어붙이기) |
| #073 | reedx04 | 갈대밭 4 | deep | L→reedp02(이어붙이기), B→reedp03 |
| #074 | reedp03 | 갈대밭 통로3 | 통로 bend | F→reedx04, R→reedx05 |
| #075 | reedx05 | 갈대밭 5 | square | L→reedp03, R→reedx06(이어붙이기) |
| #076 | reedx06 | 갈대밭 6 | wide | L→reedx05(이어붙이기), R→reedx07(이어붙이기) |
| #077 | reedx07 | 갈대밭 7 | long | L→reedx06(이어붙이기), R→reedx08(이어붙이기) |
| #078 | reedx08 | 갈대밭 8 | deep | L→reedx07(이어붙이기), B→reedp04 |
| #079 | reedp04 | 갈대밭 통로4 | 통로 bend | F→reedx08, R→reedx09(이어붙이기) |
| #080 | reedx09 | 갈대밭 9 | wide | L→reedp04(이어붙이기), R→reedx10 |
| #081 | reedx10 | 갈대밭 10 | wide | L→reedx09, →(막힘) |
| #082 | woodsx01 | 어두운 숲 1 | deep | F→woodsx02(이어붙이기) |
| #083 | woodsx02 | 어두운 숲 2 | square | B→woodsx01(이어붙이기), L→woodsp01 |
| #084 | woodsp01 | 어두운 숲 통로1 | 통로 zig | R→woodsx02, L→woodsx03(이어붙이기) |
| #085 | woodsx03 | 어두운 숲 3 | long | R→woodsp01(이어붙이기), L→woodsx04(이어붙이기) |
| #086 | woodsx04 | 어두운 숲 4 | square | R→woodsx03(이어붙이기), B→woodsx05(이어붙이기) |
| #087 | woodsx05 | 어두운 숲 5 | square | F→woodsx04(이어붙이기), B→woodsp02 |
| #088 | woodsp02 | 어두운 숲 통로2 | 통로 bend | F→woodsx05, L→woodsx06 |
| #089 | woodsx06 | 어두운 숲 6 | deep | R→woodsp02, L→woodsx07 |
| #090 | woodsx07 | 어두운 숲 7 | long | R→woodsx06, L→woodsp03(이어붙이기) |
| #091 | woodsp03 | 어두운 숲 통로3 | 통로 tunnel | R→woodsx07(이어붙이기), L→woodsx08(이어붙이기) |
| #092 | woodsx08 | 어두운 숲 8 | wide | R→woodsp03(이어붙이기), L→woodsx09 |
| #093 | woodsx09 | 어두운 숲 9 | wide | R→woodsx08, L→woodsp04(이어붙이기) |
| #094 | woodsp04 | 어두운 숲 통로4 | 통로 bend | R→woodsx09(이어붙이기), F→woodsx10 |
| #095 | woodsx10 | 어두운 숲 10 | wide | B→woodsp04, →(막힘) |
| #096 | ridgex01 | 낙엽 능선 1 | deep | B→ridgex02 |
| #097 | ridgex02 | 낙엽 능선 2 | square | F→ridgex01, R→ridgep01(이어붙이기) |
| #098 | ridgep01 | 낙엽 능선 통로1 | 통로 tunnel | L→ridgex02(이어붙이기), R→ridgex03 |
| #099 | ridgex03 | 낙엽 능선 3 | long | L→ridgep01, R→ridgex04(이어붙이기) |
| #100 | ridgex04 | 낙엽 능선 4 | wide | L→ridgex03(이어붙이기), R→ridgex05(이어붙이기) |
| #101 | ridgex05 | 낙엽 능선 5 | wide | L→ridgex04(이어붙이기), F→ridgex06(이어붙이기) |
| #102 | ridgex06 | 낙엽 능선 6 | deep | B→ridgex05(이어붙이기), F→ridgep02 |
| #103 | ridgep02 | 낙엽 능선 통로2 | 통로 bend | B→ridgex06, R→ridgex07(이어붙이기) |
| #104 | ridgex07 | 낙엽 능선 7 | long | L→ridgep02(이어붙이기), R→ridgex08(이어붙이기) |
| #105 | ridgex08 | 낙엽 능선 8 | wide | L→ridgex07(이어붙이기), R→ridgep03 |
| #106 | ridgep03 | 낙엽 능선 통로3 | 통로 zig | L→ridgex08, R→ridgex09 |
| #107 | ridgex09 | 낙엽 능선 9 | square | L→ridgep03, R→ridgep04(이어붙이기) |
| #108 | ridgep04 | 낙엽 능선 통로4 | 통로 tunnel | L→ridgex09(이어붙이기), R→ridgex10 |
| #109 | ridgex10 | 낙엽 능선 10 | square | L→ridgep04, →(막힘) |
| #110 | roofsx01 | 밤 옥상 1 | square | R→roofsx02(이어붙이기) |
| #111 | roofsx02 | 밤 옥상 2 | deep | L→roofsx01(이어붙이기), R→roofsx03 |
| #112 | roofsx03 | 밤 옥상 3 | long | L→roofsx02, R→roofsp01 |
| #113 | roofsp01 | 밤 옥상 통로1 | 통로 bend | L→roofsx03, F→roofsx04 |
| #114 | roofsx04 | 밤 옥상 4 | wide | B→roofsp01, F→roofsx05(이어붙이기) |
| #115 | roofsx05 | 밤 옥상 5 | square | B→roofsx04(이어붙이기), L→roofsp02 |
| #116 | roofsp02 | 밤 옥상 통로2 | 통로 tunnel | R→roofsx05, L→roofsx06 |
| #117 | roofsx06 | 밤 옥상 6 | wide | R→roofsp02, L→roofsp03(이어붙이기) |
| #118 | roofsp03 | 밤 옥상 통로3 | 통로 zig | R→roofsx06(이어붙이기), L→roofsx07(이어붙이기) |
| #119 | roofsx07 | 밤 옥상 7 | long | R→roofsp03(이어붙이기), L→roofsx08 |
| #120 | roofsx08 | 밤 옥상 8 | square | R→roofsx07, F→roofsp04(이어붙이기) |
| #121 | roofsp04 | 밤 옥상 통로4 | 통로 bend | B→roofsx08(이어붙이기), L→roofsx09(이어붙이기) |
| #122 | roofsx09 | 밤 옥상 9 | deep | R→roofsp04(이어붙이기), B→roofsx10 |
| #123 | roofsx10 | 밤 옥상 10 | wide | F→roofsx09, →(막힘) |
| #124 | hallx01 | 학교 복도 1 | wide | R→hallx02 |
| #125 | hallx02 | 학교 복도 2 | square | L→hallx01, R→hallx03 |
| #126 | hallx03 | 학교 복도 3 | long | L→hallx02, R→hallx04 |
| #127 | hallx04 | 학교 복도 4 | square | L→hallx03, R→hallp01 |
| #128 | hallp01 | 학교 복도 통로1 | 통로 bend | L→hallx04, B→hallx05(이어붙이기) |
| #129 | hallx05 | 학교 복도 5 | deep | F→hallp01(이어붙이기), B→hallx06(이어붙이기) |
| #130 | hallx06 | 학교 복도 6 | deep | F→hallx05(이어붙이기), R→hallp02 |
| #131 | hallp02 | 학교 복도 통로2 | 통로 tunnel | L→hallx06, R→hallx07(이어붙이기) |
| #132 | hallx07 | 학교 복도 7 | long | L→hallp02(이어붙이기), R→hallx08(이어붙이기) |
| #133 | hallx08 | 학교 복도 8 | wide | L→hallx07(이어붙이기), B→hallp03 |
| #134 | hallp03 | 학교 복도 통로3 | 통로 bend | F→hallx08, L→hallx09(이어붙이기) |
| #135 | hallx09 | 학교 복도 9 | square | R→hallp03(이어붙이기), L→hallp04 |
| #136 | hallp04 | 학교 복도 통로4 | 통로 zig | R→hallx09, L→hallx10(이어붙이기) |
| #137 | hallx10 | 학교 복도 10 | wide | R→hallp04(이어붙이기), →(막힘) |
| #138 | cabinx01 | 통나무집 1 | deep | B→cabinx02 |
| #139 | cabinx02 | 통나무집 2 | square | F→cabinx01, L→cabinp01 |
| #140 | cabinp01 | 통나무집 통로1 | 통로 zig | R→cabinx02, L→cabinx03(이어붙이기) |
| #141 | cabinx03 | 통나무집 3 | long | R→cabinp01(이어붙이기), L→cabinp02(이어붙이기) |
| #142 | cabinp02 | 통나무집 통로2 | 통로 tunnel | R→cabinx03(이어붙이기), L→cabinx04(이어붙이기) |
| #143 | cabinx04 | 통나무집 4 | square | R→cabinp02(이어붙이기), L→cabinp03 |
| #144 | cabinp03 | 통나무집 통로3 | 통로 bend | R→cabinx04, F→cabinx05(이어붙이기) |
| #145 | cabinx05 | 통나무집 5 | deep | B→cabinp03(이어붙이기), F→cabinx06(이어붙이기) |
| #146 | cabinx06 | 통나무집 6 | wide | B→cabinx05(이어붙이기), R→cabinx07(이어붙이기) |
| #147 | cabinx07 | 통나무집 7 | long | L→cabinx06(이어붙이기), R→cabinx08(이어붙이기) |
| #148 | cabinx08 | 통나무집 8 | wide | L→cabinx07(이어붙이기), B→cabinp04 |
| #149 | cabinp04 | 통나무집 통로4 | 통로 bend | F→cabinx08, R→cabinx09(이어붙이기) |
| #150 | cabinx09 | 통나무집 9 | wide | L→cabinp04(이어붙이기), F→cabinx10(이어붙이기) |
| #151 | cabinx10 | 통나무집 10 | square | B→cabinx09(이어붙이기), →(막힘) |
| #152 | libraryx01 | 도서관 1 | square | R→libraryx02(이어붙이기) |
| #153 | libraryx02 | 도서관 2 | wide | L→libraryx01(이어붙이기), R→libraryp01 |
| #154 | libraryp01 | 도서관 통로1 | 통로 tunnel | L→libraryx02, R→libraryx03 |
| #155 | libraryx03 | 도서관 3 | long | L→libraryp01, R→libraryx04 |
| #156 | libraryx04 | 도서관 4 | deep | L→libraryx03, F→libraryx05 |
| #157 | libraryx05 | 도서관 5 | wide | B→libraryx04, R→libraryp02 |
| #158 | libraryp02 | 도서관 통로2 | 통로 bend | L→libraryx05, B→libraryx06(이어붙이기) |
| #159 | libraryx06 | 도서관 6 | wide | F→libraryp02(이어붙이기), B→libraryp03(이어붙이기) |
| #160 | libraryp03 | 도서관 통로3 | 통로 bend | F→libraryx06(이어붙이기), R→libraryx07(이어붙이기) |
| #161 | libraryx07 | 도서관 7 | long | L→libraryp03(이어붙이기), R→libraryx08 |
| #162 | libraryx08 | 도서관 8 | square | L→libraryx07, B→libraryx09 |
| #163 | libraryx09 | 도서관 9 | square | F→libraryx08, L→libraryp04 |
| #164 | libraryp04 | 도서관 통로4 | 통로 zig | R→libraryx09, L→libraryx10 |
| #165 | libraryx10 | 도서관 10 | deep | R→libraryp04, →(막힘) |
| #166 | officex01 | 매표소 1 | square | R→officex02 |
| #167 | officex02 | 매표소 2 | square | L→officex01, R→officep01 |
| #168 | officep01 | 매표소 통로1 | 통로 tunnel | L→officex02, R→officex03 |
| #169 | officex03 | 매표소 3 | long | L→officep01, R→officex04(이어붙이기) |
| #170 | officex04 | 매표소 4 | deep | L→officex03(이어붙이기), R→officep02(이어붙이기) |
| #171 | officep02 | 매표소 통로2 | 통로 tunnel | L→officex04(이어붙이기), R→officex05(이어붙이기) |
| #172 | officex05 | 매표소 5 | wide | L→officep02(이어붙이기), B→officex06 |
| #173 | officex06 | 매표소 6 | deep | F→officex05, R→officep03(이어붙이기) |
| #174 | officep03 | 매표소 통로3 | 통로 zig | L→officex06(이어붙이기), R→officex07(이어붙이기) |
| #175 | officex07 | 매표소 7 | long | L→officep03(이어붙이기), R→officex08 |
| #176 | officex08 | 매표소 8 | wide | L→officex07, R→officex09(이어붙이기) |
| #177 | officex09 | 매표소 9 | wide | L→officex08(이어붙이기), R→officep04 |
| #178 | officep04 | 매표소 통로4 | 통로 bend | L→officex09, B→officex10(이어붙이기) |
| #179 | officex10 | 매표소 10 | square | F→officep04(이어붙이기), →(막힘) |
| #180 | treex01 | 나무집 속 1 | wide | B→treex02(이어붙이기) |
| #181 | treex02 | 나무집 속 2 | deep | F→treex01(이어붙이기), R→treex03(이어붙이기) |
| #182 | treex03 | 나무집 속 3 | long | L→treex02(이어붙이기), R→treep01 |
| #183 | treep01 | 나무집 속 통로1 | 통로 bend | L→treex03, F→treex04 |
| #184 | treex04 | 나무집 속 4 | square | B→treep01, L→treep02(이어붙이기) |
| #185 | treep02 | 나무집 속 통로2 | 통로 tunnel | R→treex04(이어붙이기), L→treex05 |
| #186 | treex05 | 나무집 속 5 | deep | R→treep02, B→treex06 |
| #187 | treex06 | 나무집 속 6 | wide | F→treex05, R→treex07 |
| #188 | treex07 | 나무집 속 7 | long | L→treex06, R→treep03(이어붙이기) |
| #189 | treep03 | 나무집 속 통로3 | 통로 bend | L→treex07(이어붙이기), F→treex08(이어붙이기) |
| #190 | treex08 | 나무집 속 8 | wide | B→treep03(이어붙이기), F→treex09(이어붙이기) |
| #191 | treex09 | 나무집 속 9 | square | B→treex08(이어붙이기), L→treep04 |
| #192 | treep04 | 나무집 속 통로4 | 통로 zig | R→treex09, L→treex10 |
| #193 | treex10 | 나무집 속 10 | square | R→treep04, →(막힘) |
