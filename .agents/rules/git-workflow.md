# QUY TẮC BẮT BUỘC: KỶ LUẬT GIT & QUY TRÌNH KIỂM THỬ LOCAL

> **NGUYÊN TẮC BẤT DI BẤT DỊCH (CRITICAL RULE):**
> 1. **TUYỆT ĐỐI KHÔNG commit và push trực tiếp lên nhánh `dev` hoặc `main`.**
> 2. Mọi thay đổi mã nguồn, tính năng hoặc sửa lỗi PHẢI được thực hiện trên **nhánh riêng (feature branch / bugfix branch)**: `feat/<ten-tinh-nang>` hoặc `fix/<ten-loi>`.
> 3. **BẮT BUỘC KIỂM THỬ LOCAL THÀNH CÔNG 100%:**
>    - Chạy unit test (`PYTHONPATH=src python3 -m unittest discover -s tests`).
>    - Chạy build frontend (`npm run build` hoặc check linter) nếu có thay đổi giao diện.
>    - Chỉ khi nào toàn bộ test local thành công mới được commit trên feature branch và tạo PR.
