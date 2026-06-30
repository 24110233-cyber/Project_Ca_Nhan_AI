# Project cuoi ki mon Tri tue nhan tao

Project gom cac chuong trinh mo phong thuat toan AI co giao dien truc quan. Moi moi truong duoc tach thanh mot thu muc rieng de de chay, de trinh bay va de bao tri.

## Cau truc thu muc

```text
BTVN/
+-- vaccum-8puzzle/
|   +-- algorithms/
|   +-- problems/
|   +-- ui/
|   +-- main.py
+-- to-mau/
|   +-- ac3.py
|   +-- backtracking.py
|   +-- forward_checking.py
|   +-- gui.py
|   +-- min_conflicts.py
|   +-- main.py
+-- caro/
    +-- algorithms/
    +-- problems/
    +-- ui/
    +-- main.py
```

Ghi chu: ten thu muc `vaccum-8puzzle` duoc giu theo ten da to chuc trong project.

## Yeu cau moi truong

- Python 3.10 tro len.
- Tkinter, thuong co san trong ban cai Python tren Windows.
- Khong can cai them thu vien ngoai.

Kiem tra Python:

```powershell
python --version
```

## Cach chay

Chay moi moi truong bang cach vao dung thu muc roi goi `main.py`.

### 1. Vacuum World va 8-Puzzle

```powershell
cd C:\Users\BTVN\vaccum-8puzzle
python main.py
```

Trong giao dien:

- Chon `PROBLEM`: `8-PUZZLE` hoac `VACUUM`.
- Chon `ALGORITHM`.
- Dieu chinh `MAX EXPANSIONS`, `DEPTH LIMIT`, `BEAM WIDTH K`, `MAX RESTARTS` neu can.
- Bam `EXECUTE` de chay mo phong.
- Bam `GENERATE MAP` de tao trang thai moi.
- Bam `RESET` de quay lai trang thai ban dau.

Thao tac tay:

- `W/A/S/D`: di chuyen o trong cua 8-puzzle hoac robot hut bui.
- `SPACE`: hut bui trong Vacuum World.
- Click vao o tren bang de thuc hien hanh dong hop le.

Thuat toan trong moi truong nay:

- BFS1
- BFS2
- DFS1
- DFS2
- Uniform Cost Search
- Greedy Best-First Search
- A*
- IDS
- IDA*
- Simple Hill Climbing
- Steepest-Ascent Hill Climbing
- Stochastic Hill Climbing
- Hill Climbing Random Restart
- Local Beam Search
- Simulated Annealing
- AND-OR Graph Search

Giao dien hien thi:

- Trang thai hien tai cua bai toan.
- Frontier va Reached day du.
- Trace tung buoc.
- Duong di loi giai neu thuat toan tim duoc.

Luu y: cac thuat toan cuc bo nhu Hill Climbing va Simulated Annealing co the dung o cuc tri cuc bo hoac khong tim duoc loi giai trong gioi han hien tai. Day la hanh vi dung cua nhom thuat toan local search, khong phai loi giao dien.

### 2. To mau ban do

```powershell
cd C:\Users\BTVN\to-mau
python main.py
```

Bai toan mo phong to mau ban do cac quan/huyen TP. Ho Chi Minh voi rang buoc: hai vung ke nhau khong duoc trung mau.

Thuat toan:

- Backtracking Search
- Forward Checking
- AC-3 / MAC
- Min-Conflicts

Giao dien hien thi:

- Do thi cac quan/huyen va quan he giap ranh.
- Mau da gan cho tung dinh.
- Mien gia tri con lai cua tung dinh.
- Dinh dang duoc xet.
- Nhat ky tung buoc: chon bien, thu mau, gan mau, cat tia mien gia tri, xung dot, quay lui va thanh cong.

### 3. Caro

```powershell
cd C:\Users\BTVN\caro
python main.py
```

Bai toan mo phong game Caro tren ban 7x7, dieu kien thang la 5 quan lien tiep. Trang thai gom ban co va nguoi choi dang toi luot.

Thuat toan doi khang:

- Minimax
- Alpha-Beta Pruning
- Expectimax

Trong giao dien:

- Chon thuat toan doi khang truoc khi choi.
- Human la `X`, AI la `O`.
- Click vao o trong de human danh `X`.
- Sau moi nuoc `X` hop le, AI tu dong dung thuat toan dang chon de danh `O`.
- Bam `FORCE AI MOVE` chi khi dang toi luot AI va muon ep AI tinh lai nuoc di.
- Bam `GENERATE BOARD` de tao the co ngau nhien.
- Bam `RESET` de ve ban co trong.

Giao dien hien thi:

- Ban co Caro 7x7.
- Luot hien tai `X` hoac `O`.
- So o trong con lai.
- Trang thai van co: dang choi, hoa, hoac nguoi thang.
- Trace cay tim kiem: node dang xet, frontier, reached va ghi chu danh gia/cat tia.

## Mo ta ngan gon thuat toan

### Nhom tim kiem khong thong tin va co thong tin

- BFS: mo rong node theo tung tang, dam bao tim duong di ngan nhat khi moi buoc co chi phi bang nhau.
- DFS: di sau theo mot nhanh truoc, ton it bo nho hon BFS nhung khong dam bao toi uu.
- UCS: uu tien node co chi phi duong di nho nhat.
- Greedy: uu tien node co heuristic tot nhat.
- A*: ket hop chi phi da di `g(n)` va heuristic `h(n)` bang `f(n) = g(n) + h(n)`.
- IDS: lap DFS theo do sau tang dan.
- IDA*: ket hop y tuong IDS voi nguong `f(n)` cua A*.
- AND-OR Graph Search: bieu dien bai toan co nhanh AND/OR, phu hop de mo phong cau truc ke hoach trong moi truong co kha nang mo rong sang bat dinh.

### Nhom local search

- Simple Hill Climbing: chon hang xom dau tien tot hon.
- Steepest-Ascent Hill Climbing: chon hang xom tot nhat trong tat ca hang xom.
- Stochastic Hill Climbing: chon ngau nhien trong cac hang xom tot hon.
- Random Restart Hill Climbing: chay lai hill climbing tu nhieu trang thai khoi tao.
- Local Beam Search: giu `k` trang thai tot nhat qua moi vong.
- Simulated Annealing: cho phep chap nhan nuoc di xau hon theo xac suat giam dan de thoat cuc tri cuc bo.

### Nhom CSP

- Backtracking: gan gia tri tung bien va quay lui khi vi pham rang buoc.
- Forward Checking: sau khi gan bien, cat bo gia tri khong hop le khoi mien cua cac bien ke.
- AC-3 / MAC: duy tri tinh nhat quan cung trong qua trinh gan bien.
- Min-Conflicts: bat dau tu mot gan day du, sau do sua cac bien dang xung dot de giam tong so xung dot.

### Nhom doi khang

- Minimax: gia dinh hai nguoi choi toi uu, mot ben toi da hoa diem va ben kia toi thieu hoa diem.
- Alpha-Beta: cai tien Minimax bang cat tia cac nhanh khong can xet.
- Expectimax: thay node doi thu bang node ki vong, phu hop khi doi thu duoc mo hinh nhu hanh vi co tinh xac suat.

## Kiem tra da thuc hien

Da chay smoke test bang Python cho toan bo project:

- Kiem tra cu phap tat ca file `.py`: dat.
- `vaccum-8puzzle`: tat ca thuat toan trong registry chay duoc voi 8-puzzle va vacuum, tra ve `SearchResult` hop le.
- `caro`: Minimax, Alpha-Beta va Expectimax tinh duoc nuoc di tren the co mau.
- `to-mau`: Backtracking, Forward Checking, AC-3 va Min-Conflicts deu tim duoc loi giai hop le, 22 vung duoc to mau va khong co xung dot.

