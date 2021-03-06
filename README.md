# Система клиент-серверного взаимодействия
## Описание
Система является оболочкой для базового обмена сообщениями(командами), основанного на TCP.
Разделяется на 2 отдельных приложения:
- клиентское приложение
- серверное приложение

В данном проекте разработан и реализован механизм обхода ограничения протокола TCP в виде максимального окна сообщений (по умолчанию 1024 байт). Проект не подразумевает никакого непосредственного использования, однако может быть использован для осуществления и обработки клиент-серверного взаимодействия других систем.
## Ветки разработки/использования
На данном этапе присутствуют 2 ветки разработки:
- [master](https://github.com/omelched/client-server-unittest/tree/master) - стабильная продакшн-ветка
- [creating-tests](https://github.com/omelched/client-server-unittest/tree/creating-tests) - нестабильная ветка разработки

На продакшн-ветке ~~вроде бы~~ всё работает.
На ветке разработки не обязательно, использовать на страх и риск.
## Запуск
Для запуска необходимо иметь установленный интерпретатор python, версии не ниже 3.7 (версии ниже ещё не тестировались).
Процесс запуска:
1.  Скачать ветку.
2.  ~~Запустить в IDE~~ Выполнить команду оболочки `python start_server.py` для запуска сервера.
3.  ~~Запустить в IDE~~ Выполнить команду оболочки `python start_client.py` для запуска клиента.
## Команды в приложениях
Вызов команд происходит в виде строки формата `<имя_команды>:<агрументы(опционально)>` без кавычек соответственно.
- Сервер
  - list - отображает список подключенных клиентов;
  - stop / q - останавливает сервер.
- Клиент
  - s - передает команду на сервер напечатать аргумент команды клиента;
  - sd - то же самое, только в целях отладки - сообщения взаимодействия будут отправляться по-очереди по команде пользователя <Enter>;
  - q - останавливает клиент.
