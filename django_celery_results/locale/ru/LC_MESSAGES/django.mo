��    )      d  ;   �      �  $   �  $   �  #   �               )     I  #   Z  7   ~  2   �  6   �  1         R  H   [  =   �  B   �  I   %     o  
   �     �     �     �     �  F   �            	   5     ?     T  
   n  /   y  U   �  .   �  	   .     8     ?     ]     j     x     �  F  �  0   �	  F   	
     P
     g
  +   �
  9   �
  '   �
  =     Y   O  Q   �  N   �  P   J     �  h   �  O     L   d  �   �  F   3     z     �  ,   �  !   �  '   �  �        �  )   �     �  6   �     .     N  '   h  �   �  m     	   �     �  ;   �     �     �          8         #                  %                                                       	            $                   )              
                       !   &   '           "                   (             Celery ID for the Chord header group Celery ID for the Group that was run Celery ID for the Task that was run Celery Results Completed DateTime Content type of the result data Created DateTime Current state of the task being run Datetime field when the group result was created in UTC Datetime field when the group was completed in UTC Datetime field when the task result was created in UTC Datetime field when the task was completed in UTC Group ID JSON meta information about the task, such as information on child tasks JSON representation of the named arguments used with the task JSON representation of the positional arguments used with the task JSON serialized list of task result tuples. use .group_result() to decode Name of the Task which was run Parameters Result Result Content Type Result Data Result Encoding Starts at len(chord header) and decrements after each task is finished Task ID Task Meta Information Task Name Task Named Arguments Task Positional Arguments Task State Text of the traceback if the task generated one The data returned by the task.  Use content_encoding and content_type fields to read. The encoding used to save the task result data Traceback Worker Worker that executes the task group result group results task result task results Project-Id-Version: 
Report-Msgid-Bugs-To: 
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator:  ILDAR MINNAKHMETOV <ildarworld@gmail.com>
Language-Team: LANGUAGE <LL@li.org>
Language: ru
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=2; plural=(n != 1);
 Celery ID для заголовка группы Celery ID для группы которая была запущена Celery ID задачи Результаты Celery Дата и время завершения Тип контента данных результата Дата и время создания Текущий статус запущенной задачи Дата и время если результат группы был создан (UTC) Дата и время, когда группа была завершена (UTC) Дата и время когда результат был создан (UTC) Дата и время когда задача была завершена (UTC) ID группы JSON мета-информация о задаче, к примеру о дочерних задачах JSON с именованными аргументами задачи (**kwargs) JSON с позиционными аргументами задачи (*args) JSON-список кортежей результата. Используйте .group_result() для декодирования Название задачи которая была запущена Параметры Результаты Тип контента результата Данные результата Кодировка результата Начинается в len(chord header) и уменьшается после каждого завершенного задания ID Задачи Метаинформация задачи Название задачи Именованные аргументы задачи Аргументы задачи Статус задачи Текст traceback, если есть Данные, которые вернула задача. Используйте content_encoding и content_type для чтения. Кодировка использованная для сохранения данных результата Traceback Воркер Воркер который выполняет задачу результат группы результаты групп результат задачи результаты задач 