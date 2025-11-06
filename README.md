# Privuew Landing Management

Проект переведён на стек Python 3.6.8 и использует Flask для выдачи лендинга, страницы входа и панели управления. Вся логика работы с контентом и почтовой отправкой реализована на стороне сервера в файле `app.py`.

## Структура проекта
- `public/landingStart.html` — основной лендинг, который подгружает контент через REST API.
- `public/mobile.html` — облегчённая мобильная версия с укрупнёнными блоками и адаптированной формой заявки.
- `public/login.html` — страница авторизации администратора.
- `public/admin.html` — панель управления для изменения текстов, ссылок и всех изображений.
- `public/index.html` — файл-редирект на основной лендинг.
- `data/content.json` — данные лендинга, редактируемые через панель.
- `data/adminCredentials.json` — логин и пароль администратора (меняются редактированием файла).
- `app.py` — сервер Flask, отдающий статику и обрабатывающий API-запросы.
- `requirements.txt` — список Python-зависимостей.
- `scripts/check_conflicts.py` — утилита проверки конфликтных маркеров в файлах.

## Быстрый старт в окружении Python 3.6.8
1. Перейдите в каталог проекта и создайте виртуальное окружение:
   ```bash
   python3.6 -m venv venv
   source venv/bin/activate
   ```
2. Установите зависимости:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Запустите сервер:
   ```bash
   python app.py
   ```
4. Откройте `http://localhost:9090/` — на мобильных устройствах произойдёт редирект на мобильную версию (`/mobile`), на десктопе откроется основной лендинг. Страница входа находится на `http://localhost:9090/login`, панель управления — на `http://localhost:9090/admin`.

> Если на хостинге уже активирована системная оболочка Python 3.6.8, достаточно выполнить команды установки зависимостей и запуска без создания виртуального окружения (или использовать `python3.6 -m venv`, если доступно).

## Установка pip для Python 3.6.8
Если на сервере отсутствует `pip`, выполните следующие команды перед установкой зависимостей:

```bash
# Попробовать встроенную установку pip
python3.6 -m ensurepip --upgrade || true

# Если ensurepip недоступен, скачать и установить через get-pip.py
curl -fsSL https://bootstrap.pypa.io/pip/3.6/get-pip.py -o get-pip.py
python3.6 get-pip.py --user
rm -f get-pip.py

# После появления pip обновите его и набор базовых инструментов
python3.6 -m pip install --upgrade pip setuptools wheel
```

Далее используйте `python3.6 -m pip install -r requirements.txt` или активируйте виртуальное окружение и работайте командой `pip install -r requirements.txt`.

### Что означает предупреждение «WARNING: The scripts pip, pip3 and pip3.6 are installed in ... which is not on PATH»
Если `pip` устанавливается с ключом `--user`, исполняемые файлы попадают в каталог `~/.local/bin`. На некоторых хостингах (например, `~/data/.local/bin` или `/var/www/<user>/data/.local/bin`) эта папка не добавлена в `PATH`, поэтому оболочка выводит сообщение:

```
WARNING: The scripts pip, pip3 and pip3.6 are installed in '/var/www/<user>/data/.local/bin' which is not on PATH.
```

Это означает, что `pip` установлен успешно, но оболочка не сможет найти исполняемые файлы без полного пути. Добавьте каталог `~/.local/bin` в переменную окружения `PATH`, чтобы запускать `pip` и другие утилиты напрямую:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

После обновления `PATH` предупреждение исчезнет, а команды вроде `pip3.6 --version` или `pip install -r requirements.txt` будут работать без дополнительных путей.

## Установка зависимостей через Git (без pip)
Если на хостинге запрещено использовать `pip`, зависимости можно скачать напрямую из репозиториев Git и установить классическим
`setup.py`. Ниже пример для окружения, в котором проект находится в каталоге
`/www/dsfasfdsfdfffd.ru/privuew` (при необходимости подставьте свой абсолютный путь).

```bash
# 1. Создаём структуру каталогов для проекта и сторонних библиотек
mkdir -p /www/dsfasfdsfdfffd.ru/privuew
mkdir -p /www/dsfasfdsfdfffd.ru/privuew/vendor

# 2. Задаём полный путь до проекта и каталог для сторонних библиотек
export PROJECT_ROOT=/www/dsfasfdsfdfffd.ru/privuew
export VENDOR_DIR=/www/dsfasfdsfdfffd.ru/privuew/vendor

# 3. Клонируем нужные версии библиотек (Flask и её зависимости)
git clone --branch 2.0.3 https://github.com/pallets/flask.git \
    "$VENDOR_DIR"/flask-2.0.3
git clone --branch 2.0.3 https://github.com/pallets/werkzeug.git \
    "$VENDOR_DIR"/werkzeug-2.0.3
git clone --branch 3.0.3 https://github.com/pallets/jinja.git \
    "$VENDOR_DIR"/jinja2-3.0.3
git clone --branch 2.0.1 https://github.com/pallets/itsdangerous.git \
    "$VENDOR_DIR"/itsdangerous-2.0.1
git clone --branch 2.0.1 https://github.com/pallets/markupsafe.git \
    "$VENDOR_DIR"/markupsafe-2.0.1
git clone --branch 8.0.4 https://github.com/pallets/click.git \
    "$VENDOR_DIR"/click-8.0.4
git clone --branch v2.26.0 https://github.com/psf/requests.git \
    "$VENDOR_DIR"/requests-2.26.0
git clone --branch 1.26.20 https://github.com/urllib3/urllib3.git \
    "$VENDOR_DIR"/urllib3-1.26.20
git clone --branch 2021.05.30 https://github.com/certifi/python-certifi.git \
    "$VENDOR_DIR"/certifi-2021.05.30
git clone --branch 2.0.12 https://github.com/Ousret/charset_normalizer.git \
    "$VENDOR_DIR"/charset-normalizer-2.0.12
git clone --branch v3.3 https://github.com/kjd/idna.git \
    "$VENDOR_DIR"/idna-3.3
git clone --branch 4.10.0 https://github.com/wention/BeautifulSoup4.git \
    "$VENDOR_DIR"/beautifulsoup4-4.10.0
git clone --branch v2.8.0 https://github.com/facelessuser/soupsieve.git \
    "$VENDOR_DIR"/soupsieve-2.8.0

# 4. Устанавливаем каждую библиотеку в пользовательский каталог Python 3.6.8
cd "$VENDOR_DIR"/flask-2.0.3 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/werkzeug-2.0.3 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/jinja2-3.0.3 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/itsdangerous-2.0.1 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/markupsafe-2.0.1 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/click-8.0.4 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/urllib3-1.26.20 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/certifi-2021.05.30 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/charset-normalizer-2.0.12 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/idna-3.3 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/requests-2.26.0 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/soupsieve-2.8.0 && python3.6 setup.py install --user
cd "$VENDOR_DIR"/beautifulsoup4-4.10.0 && python3.6 setup.py install --user

# 5. (Опционально) Добавляем vendor-директорию в PYTHONPATH,
# если не выполняли setup.py install, а хотите использовать пакеты напрямую из исходников
# echo "export PYTHONPATH=\"$VENDOR_DIR/flask-2.0.3/src:$PYTHONPATH\"" >> ~/.bashrc
```

Команда `python3.6 setup.py install --user` установит библиотеку в каталог `~/.local/lib/python3.6/site-packages`. Убедитесь, что он
находится в `PYTHONPATH` (обычно добавляется автоматически). После установки всех зависимостей запустите сервер командой
`python3.6 /www/dsfasfdsfdfffd.ru/privuew/app.py`.

## Работа с панелью управления
1. Откройте `http://<домен>/login`, введите логин и пароль из `data/adminCredentials.json` (по умолчанию `admin`/`1234`).
2. После входа происходит переадресация в `http://<домен>/admin`. Панель подгрузит данные из `content.json`; пока идёт загрузка, кнопка «Сохранить изменения» неактивна.
3. Изменяйте тексты, ссылки и изображения в соответствующих разделах. Отдельный блок «Логотипы» отвечает за изображения в шапке и hero-блоке, раздел «Наши партнёры» позволяет добавлять логотипы, ссылки и задавать интервал автопрокрутки (в секундах), а секция «Заявки» содержит адрес электронной почты и параметры SMTP для отправки форм.
   Панель разбита на две вкладки: «Версия для ПК» и «Мобильная версия». Во второй вкладке доступны компактные поля для мобильного лендинга — они не дублируют общие настройки (например, SMTP или контакты для десктопа).
4. После правок нажмите «Сохранить изменения». Панель передаст обновлённый `content.json` на сервер, и лендинг сразу подхватит новые данные.

## Отзывы и блок партнёров
- При открытии страницы клиент запрашивает свежие отзывы с 2ГИС (`https://2gis.ru/norilsk/firm/70000001047366044/tab/reviews`). Если загрузка успешна, они заменяют локальные данные; при ошибке или отсутствии доступа отображаются отзывы из `content.json`.
- Блок партнёров отображает пять логотипов, автоматически прокручивая список по одному элементу. При наведении логотип становится цветным, а клик открывает сайт партнёра в новой вкладке. Интервал автопрокрутки задаётся в панели управления.

### Переменные окружения для 2ГИС
- `EXTERNAL_REVIEWS_URL` — при необходимости укажите другой URL страницы 2ГИС.
- `EXTERNAL_REVIEWS_TIMEOUT` — таймаут запроса (в секундах, по умолчанию 10).
- `EXTERNAL_REVIEWS_LIMIT` — максимальное количество отзывов, которое вернёт сервер (по умолчанию 20).
- `EXTERNAL_REVIEWS_DISABLE_PROXY` — установите `1`, если нужно игнорировать переменные `HTTP(S)_PROXY` при обращении к 2ГИС.

## Модальное окно заявки
- Кнопки CTA открывают модальное окно с формой заявки и логотипом компании.
- Обязательные поля: «Имя» и «E-mail». При ошибке под полем появляется красная подсказка.
- Допускается прикрепление файла размером до 20 МБ (значение можно изменить переменной `MAX_ATTACHMENT_SIZE_BYTES`). При превышении лимита сервер вернёт ошибку.
- После успешной отправки письмо приходит на `etl@elektrokonstruktiv.ru` (адрес можно изменить в панели управления в разделе «Заявки»), окно закрывается, а пользователь видит уведомление «Ваша заявка отправлена…».

## Почтовая отправка
Форма заявок отправляется через SMTP. Основные параметры (сервер, порт, тип шифрования, логин и пароль) можно задать прямо в панели управления в разделе «Заявки» — значения сохраняются в `content.json` и применяются без перезапуска сервера. Если панель недоступна, используйте переменные окружения:
- `SMTP_HOST` — адрес почтового сервера.
- `SMTP_PORT` — порт (по умолчанию 587).
- `SMTP_SECURITY` — режим шифрования: `none`, `starttls` или `ssl` (по умолчанию `starttls`). Для обратной совместимости поддерживается переменная `SMTP_SECURE` (`true` включает `starttls`).
- `SMTP_USER`, `SMTP_PASSWORD` — учётные данные (если SMTP-сервер требует авторизацию).
- `REQUEST_FROM_EMAIL` — адрес отправителя (по умолчанию `no-reply@elektrokonstruktiv.ru`).
- `REQUEST_TARGET_EMAIL` — адрес получателя (по умолчанию `etl@elektrokonstruktiv.ru`).

## Проверка на конфликтные маркеры
```bash
python scripts/check_conflicts.py
```
Скрипт сообщит, если найдёт последовательности, напоминающие неразрешённые маркеры Git (семь символов `<`, `=` или `>` подряд).

## Выгрузка в удалённый репозиторий
1. Создайте пустой репозиторий на GitHub и скопируйте его URL (например, `https://github.com/NektoGurov/privuew.git`).
2. Добавьте удалённый адрес:
   ```bash
   git remote add origin https://github.com/NektoGurov/privuew.git
   ```
3. Убедитесь, что изменения закоммичены: `git status`.
4. Отправьте коммиты:
   ```bash
   git push -u origin main
   ```

## Скачивание проекта с Git на хостинге

Если на сервере доступен Git, воспользуйтесь стандартным клонированием:

```bash
git clone https://github.com/<ваш-аккаунт>/<ваш-репозиторий>.git
cd <ваш-репозиторий>
```

Когда Git недоступен, проект можно загрузить через Python-скрипт
`scripts/download_repo.py`, который скачивает ZIP-архив выбранной ветки и
распаковывает его в указанную директорию.

1. Скопируйте каталог `scripts/` на хостинг или создайте в рабочей папке
   файл `scripts/download_repo.py` из репозитория.
2. Выполните:
   ```bash
   python3.6 scripts/download_repo.py --repo https://github.com/<аккаунт>/<репозиторий>.git \
       --branch main --dest /path/to/project
   ```
   Скрипт создаст каталог `/path/to/project`, скачает ZIP-архив ветки `main`
   и распакует содержимое. При необходимости укажите другое имя ветки и путь
   назначения.
3. Перейдите в распакованный каталог и продолжайте установку зависимостей по
   инструкциям из раздела «Быстрый старт».

## Развёртывание в Docker (Python 3.6)
1. Соберите образ:
   ```bash
   docker build -t privuew-app .
   ```
2. Запустите контейнер, пробросив порт 9090:
   ```bash
   docker run -d --name privuew-app -p 9090:9090 privuew-app
   ```
3. При необходимости сохраняйте каталог `data/` между перезапусками через volume: `-v $(pwd)/data:/app/data`.

## Развёртывание на классическом хостинге
1. Скопируйте на сервер весь проект (каталоги `public/`, `data/`, `scripts/`, файлы `app.py`, `requirements.txt`, `Dockerfile`, `README.md`). Убедитесь, что `data/` доступна для записи.
2. Установите зависимости с помощью `pip install -r requirements.txt` (при необходимости создайте виртуальное окружение через `python3.6 -m venv venv`).
3. Запустите сервер:
   ```bash
   python app.py
   ```
   или используйте любой WSGI-сервер (gunicorn/uwsgi), передав объект `app` из `app.py`.
4. Настройте прокси-сервер (Nginx/Apache), чтобы запросы к `/`, `/login`, `/admin` и `/api/*` проксировались во Flask-приложение. Статические файлы можно отдавать напрямую из каталога `public/`.
5. Для работы по HTTPS установите `COOKIE_SECURE=true`, чтобы авторизационная cookie помечалась как `Secure`.

## Настройка домена `http://www.dsfasfdsfdfffd.ru/`
1. Направьте DNS-запись домена на сервер с приложением.
2. Запустите Flask-сервер на порту 80 (`PORT=80 python app.py`) или настройте прокси, который будет перенаправлять трафик с 80/443 портов на приложение (по умолчанию оно слушает порт 9090).
3. После запуска домен `http://www.dsfasfdsfdfffd.ru/` отдаст лендинг, а `http://www.dsfasfdsfdfffd.ru/admin` — форму входа.

## Куда копировать файлы при переносе
Сохраните структуру каталогов:
- `public/` — статические файлы (HTML, CSS, изображения, шрифты).
- `data/` — контент и учётные данные (должны быть доступны для чтения/записи).
- `app.py` — сервер.
- `requirements.txt` — зависимости.
- `scripts/` — вспомогательные утилиты (например, проверка конфликтов).
- `Dockerfile` — сценарий сборки контейнера.

После копирования установите зависимости и запустите сервер, как описано выше.